from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance.base import GovernanceDecision
from app.memory.models import MemoryContext
from app.models.api import ChatRequest, ChatResponse, OrchestrationMetadata, ToolExecutionResponse
from app.orchestration.context import ExecutionContext, ToolPlan
from app.rag.retriever import RetrievalResult


class PipelineStage(StrEnum):
    REQUEST_RECEIVED = "RequestReceived"
    CONTEXT_INITIALIZED = "ContextInitialized"
    RETRIEVAL_PHASE = "RetrievalPhase"
    GOVERNANCE_PHASE = "GovernancePhase"
    AGENT_SELECTION_PHASE = "AgentSelectionPhase"
    TOOL_DECISION_PHASE = "ToolDecisionPhase"
    TOOL_EXECUTION_PHASE = "ToolExecutionPhase"
    PROMPT_ASSEMBLY_PHASE = "PromptAssemblyPhase"
    LLM_GENERATION_PHASE = "LLMGenerationPhase"
    RESPONSE_SYNTHESIS_PHASE = "ResponseSynthesisPhase"
    AUDIT_PHASE = "AuditPhase"
    RESPONSE_COMPLETED = "ResponseCompleted"


TokenEmitter = Callable[[str], Awaitable[None]]


@dataclass(slots=True)
class PipelineExecutionState:
    session: AsyncSession
    request: ChatRequest
    context: ExecutionContext | None = None
    retrieval: RetrievalResult | None = None
    memory: MemoryContext | None = None
    governance_decision: GovernanceDecision | None = None
    tool_plan: ToolPlan | None = None
    tool_response: ToolExecutionResponse | None = None
    response_text: str | None = None
    orchestration: OrchestrationMetadata | None = None
    provider_name: str | None = None
    model_name: str | None = None
    selected_agent: str | None = None
    stream_callback: TokenEmitter | None = None


@dataclass(slots=True, frozen=True)
class PipelineExecutionResult:
    context: ExecutionContext
    response_text: str
    provider_name: str
    model_name: str
    orchestration: OrchestrationMetadata

    def to_chat_response(self) -> ChatResponse:
        return ChatResponse(
            conversation_id=self.context.conversation_id or "",
            response=self.response_text,
            citations=list(self.context.citations),
            provider=self.provider_name,
            model=self.model_name,
            orchestration=self.orchestration,
        )
