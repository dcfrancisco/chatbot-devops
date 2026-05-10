from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models import ConversationMessage, MemoryEntry


@dataclass(slots=True, frozen=True)
class MemoryRelevanceExplanation:
    memory_id: str
    memory_type: str
    similarity_score: float
    importance_score: float
    relevance_score: float
    reason: str


@dataclass(slots=True, frozen=True)
class MemoryMatch:
    entry: MemoryEntry
    explanation: MemoryRelevanceExplanation


@dataclass(slots=True)
class MemoryContext:
    recent_messages: list[ConversationMessage]
    relevant_memories: list[MemoryEntry]
    episodic_memories: list[MemoryEntry] = field(default_factory=list)
    semantic_memories: list[MemoryEntry] = field(default_factory=list)
    summary_memories: list[MemoryEntry] = field(default_factory=list)
    relevance_matches: list[MemoryMatch] = field(default_factory=list)

    def explainable_retrieval(self) -> list[str]:
        return [
            f"{match.entry.memory_type}:{match.entry.key} score={match.explanation.relevance_score:.3f} reason={match.explanation.reason}"
            for match in self.relevance_matches
        ]