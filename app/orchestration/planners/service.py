from app.memory.service import MemoryContext
from app.models.llm import LLMMessage
from app.orchestration.planners.interfaces import PromptPlanner
from app.rag.retriever import RetrievalResult


class PromptAssemblyService(PromptPlanner):
    def build_messages(
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
            "You are a local AI runtime agent operating inside a modular orchestration platform. "
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