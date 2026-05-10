from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.db.models import Conversation
from app.memory.service import MemoryContext
from app.models.api import Citation, OrchestrationMetadata
from app.models.llm import LLMMessage
from app.rag.retriever import RetrievalResult


@dataclass(slots=True)
class ToolPlan:
    name: str
    arguments: dict[str, object]


@dataclass(slots=True)
class ExecutionStep:
    name: str
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrchestrationRuntimeState:
    trace_id: str
    agent_name: str
    conversation_id: str | None
    route_name: str = "deterministic"
    selected_tool: str | None = None
    steps: list[ExecutionStep] = field(default_factory=list)

    def record(self, name: str, **metadata: Any) -> None:
        self.steps.append(ExecutionStep(name=name, metadata=metadata))


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
    blocked_response_text: str | None
    runtime_state: OrchestrationRuntimeState