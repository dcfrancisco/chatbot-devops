from __future__ import annotations

from typing import Protocol

from app.orchestration.state.models import ToolPlan
from app.rag.retriever import RetrievalResult


class RequestRouter(Protocol):
    def route(self, user_message: str, retrieval: RetrievalResult) -> ToolPlan | None:
        ...