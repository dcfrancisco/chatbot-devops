from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.models import Conversation, ConversationMessage, MessageCitation
from app.models.api import (
    ChatRequest,
    ChatResponse,
    Citation,
    OrchestrationMetadata,
    ToolExecutionRequest,
    ToolInvocationSummary,
)
from app.models.llm import LLMMessage
from app.rag.retriever import RetrievalResult, RetrieverService
from app.services.llm import OpenAICompatibleProvider
from app.services.memory_service import MemoryContext, MemoryService
from app.tools.service import ToolExecutionService


@dataclass(slots=True)
class ToolPlan:
    name: str
    arguments: dict[str, object]


@dataclass(slots=True)
class TurnContext:
    trace_id: str
    conversation: Conversation
    retrieval: RetrievalResult
    memory: MemoryContext
    citations: list[Citation]
    messages: list[LLMMessage]
    orchestration: OrchestrationMetadata
    tool_response_text: str | None


class OrchestrationService:
    def __init__(
        self,
        settings: Settings,
        llm_provider: OpenAICompatibleProvider,
        retriever_service: RetrieverService,
        memory_service: MemoryService,
        tool_execution_service: ToolExecutionService,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._retriever_service = retriever_service
        self._memory_service = memory_service
        self._tool_execution_service = tool_execution_service
        self._logger = get_logger(__name__)

    async def run(self, session: AsyncSession, request: ChatRequest) -> ChatResponse:
        turn = await self._prepare_turn(session, request)
        user_message = await self._store_message(
            session,
            conversation_id=turn.conversation.id,
            role="user",
            content=request.message,
            citations=[],
            metadata_json={"orchestration_trace_id": turn.trace_id},
        )
        await self._memory_service.remember_user_message(
            session,
            conversation_id=turn.conversation.id,
            message_index=user_message.message_index,
            content=request.message,
        )
        response_text = await self._llm_provider.generate(turn.messages)
        await self._store_message(
            session,
            conversation_id=turn.conversation.id,
            role="assistant",
            content=response_text,
            citations=turn.citations,
            metadata_json={
                "orchestration_trace_id": turn.trace_id,
                "tool_used": turn.orchestration.tool_invocation.model_dump() if turn.orchestration.tool_invocation else None,
            },
        )
        await session.commit()
        return ChatResponse(
            conversation_id=turn.conversation.id,
            response=response_text,
            citations=turn.citations,
            provider=self._llm_provider.provider_name,
            model=self._llm_provider.chat_model,
            orchestration=turn.orchestration,
        )

    async def stream_run(self, session: AsyncSession, request: ChatRequest) -> AsyncIterator[str]:
        turn = await self._prepare_turn(session, request)
        user_message = await self._store_message(
            session,
            conversation_id=turn.conversation.id,
            role="user",
            content=request.message,
            citations=[],
            metadata_json={"orchestration_trace_id": turn.trace_id},
        )
        await self._memory_service.remember_user_message(
            session,
            conversation_id=turn.conversation.id,
            message_index=user_message.message_index,
            content=request.message,
        )

        accumulated: list[str] = []
        async for token in self._llm_provider.generate_stream(turn.messages):
            accumulated.append(token)
            yield self._format_sse({"type": "token", "delta": token})

        response_text = "".join(accumulated)
        await self._store_message(
            session,
            conversation_id=turn.conversation.id,
            role="assistant",
            content=response_text,
            citations=turn.citations,
            metadata_json={
                "orchestration_trace_id": turn.trace_id,
                "tool_used": turn.orchestration.tool_invocation.model_dump() if turn.orchestration.tool_invocation else None,
            },
        )
        await session.commit()
        yield self._format_sse(
            {
                "type": "done",
                "conversation_id": turn.conversation.id,
                "citations": [citation.model_dump() for citation in turn.citations],
                "provider": self._llm_provider.provider_name,
                "model": self._llm_provider.chat_model,
                "orchestration": turn.orchestration.model_dump(mode="json"),
            }
        )

    async def _prepare_turn(self, session: AsyncSession, request: ChatRequest) -> TurnContext:
        trace_id = str(uuid4())
        conversation = await self._get_or_create_conversation(session, request.conversation_id)
        retrieval = await self._retriever_service.search(session, request.message)
        memory = await self._memory_service.build_context(
            session,
            conversation_id=conversation.id,
            query=request.message,
        )
        tool_plan = self._determine_tool_plan(request.message, retrieval)
        tool_response_text = None
        tool_invocation = None
        if tool_plan is not None:
            tool_response = await self._tool_execution_service.execute(
                session,
                ToolExecutionRequest(name=tool_plan.name, arguments=tool_plan.arguments),
            )
            tool_invocation = ToolInvocationSummary(
                name=tool_response.name,
                status=tool_response.status,
                trace_id=tool_response.trace.trace_id,
            )
            tool_response_text = json.dumps(tool_response.model_dump(mode="json"), ensure_ascii=True)

        orchestration = OrchestrationMetadata(
            trace_id=trace_id,
            retrieval_count=len(retrieval.citations),
            memory_count=len(memory.relevant_memories),
            tool_invocation=tool_invocation,
        )
        messages = self._build_messages(request.message, retrieval, memory, tool_response_text)
        self._logger.info(
            "orchestration_prepared",
            extra={
                "trace_id": trace_id,
                "conversation_id": conversation.id,
                "retrieval_count": len(retrieval.citations),
                "memory_count": len(memory.relevant_memories),
                "tool_name": tool_plan.name if tool_plan else None,
            },
        )
        return TurnContext(
            trace_id=trace_id,
            conversation=conversation,
            retrieval=retrieval,
            memory=memory,
            citations=retrieval.citations,
            messages=messages,
            orchestration=orchestration,
            tool_response_text=tool_response_text,
        )

    def _build_messages(
        self,
        user_message: str,
        retrieval: RetrievalResult,
        memory: MemoryContext,
        tool_response_text: str | None,
    ) -> list[LLMMessage]:
        history_messages = [
            LLMMessage(role=message.role, content=message.content)
            for message in memory.recent_messages
            if message.role in {"user", "assistant"}
        ]
        memory_context = "\n".join(f"- {entry.content}" for entry in memory.relevant_memories)
        retrieval_context = "\n\n".join(retrieval.context_blocks)
        tool_context = tool_response_text or "No tool executed."
        system_prompt = (
            "You are a local AI DevOps assistant using a lightweight orchestration flow. "
            "Work retrieval-first. Use tool results only when they were explicitly provided. "
            "Be deterministic where possible, cite retrieved sources when relevant, and state uncertainty clearly. "
            "Do not invent tool outputs or hidden state."
        )
        user_payload = (
            f"Retrieved context:\n{retrieval_context or 'No relevant documents found.'}\n\n"
            f"Conversation memory:\n{memory_context or 'No relevant memory found.'}\n\n"
            f"Tool output:\n{tool_context}\n\n"
            f"User question: {user_message}"
        )
        return [LLMMessage(role="system", content=system_prompt), *history_messages, LLMMessage(role="user", content=user_payload)]

    def _determine_tool_plan(self, user_message: str, retrieval: RetrievalResult) -> ToolPlan | None:
        lowered = user_message.lower()
        retrieval_is_thin = len(retrieval.citations) < 2

        if self._should_use_jenkins_tool(lowered, retrieval_is_thin):
            if "list" in lowered and "job" in lowered:
                return ToolPlan(name="jenkins", arguments={"action": "list_jobs"})
            if any(marker in lowered for marker in ("details for job", "job details", "show job")):
                job_name = self._extract_named_value(user_message, markers=["job", "named"])
                if job_name:
                    return ToolPlan(name="jenkins", arguments={"action": "get_job", "name": job_name})

        if self._should_use_api_tool(lowered):
            integration = self._extract_named_value(user_message, markers=["integration", "service"])
            path = self._extract_path(user_message)
            if integration and path:
                return ToolPlan(
                    name="api",
                    arguments={
                        "integration": integration,
                        "method": "GET",
                        "path": path,
                    },
                )

        return None

    def _should_use_jenkins_tool(self, lowered: str, retrieval_is_thin: bool) -> bool:
        return retrieval_is_thin and "jenkins" in lowered and any(
            marker in lowered for marker in ("list job", "list jobs", "show job", "job details")
        )

    def _should_use_api_tool(self, lowered: str) -> bool:
        return any(marker in lowered for marker in ("call api", "fetch api", "query api", "integration"))

    def _extract_named_value(self, text: str, *, markers: list[str]) -> str | None:
        stripped = text.replace("'", " ").replace('"', " ")
        tokens = stripped.split()
        lowered_tokens = [token.lower() for token in tokens]
        for index, token in enumerate(lowered_tokens):
            if token in markers and index + 1 < len(tokens):
                candidate = tokens[index + 1].strip(" ,.:;")
                if candidate and not candidate.startswith("/"):
                    return candidate
        return None

    def _extract_path(self, text: str) -> str | None:
        for token in text.split():
            if token.startswith("/"):
                return token.strip(" ,.;")
        return None

    async def _get_or_create_conversation(self, session: AsyncSession, conversation_id: str | None) -> Conversation:
        if conversation_id is not None:
            conversation = await session.get(Conversation, conversation_id)
            if conversation is not None:
                return conversation
        conversation = Conversation()
        session.add(conversation)
        await session.flush()
        return conversation

    async def _store_message(
        self,
        session: AsyncSession,
        *,
        conversation_id: str,
        role: str,
        content: str,
        citations: list[Citation],
        metadata_json: dict,
    ) -> ConversationMessage:
        current_max_index = await session.scalar(
            select(ConversationMessage.message_index)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.message_index))
            .limit(1)
        )
        message = ConversationMessage(
            conversation_id=conversation_id,
            message_index=(current_max_index or 0) + 1,
            role=role,
            content=content,
            citations=[citation.model_dump() for citation in citations],
            metadata_json=metadata_json,
        )
        session.add(message)
        await session.flush()
        for rank, citation in enumerate(citations, start=1):
            session.add(
                MessageCitation(
                    message_id=message.id,
                    document_chunk_id=citation.chunk_id,
                    citation_rank=rank,
                    score=citation.score,
                    snippet=citation.snippet,
                    metadata_json={"source_id": citation.source_id, "document_title": citation.document_title},
                )
            )
        return message

    def _format_sse(self, payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"