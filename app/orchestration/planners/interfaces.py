from __future__ import annotations

from typing import Protocol

from app.memory.service import MemoryContext
from app.models.llm import LLMMessage
from app.rag.retriever import RetrievalResult


class PromptPlanner(Protocol):
    def build_messages(
        self,
        user_message: str,
        retrieval: RetrievalResult,
        memory: MemoryContext,
        tool_response_text: str | None,
    ) -> list[LLMMessage]:
        ...