from app.db.models import MemoryEntry
from app.llm.base import BaseLLMProvider
from app.memory.models import MemoryMatch, MemoryRelevanceExplanation


class RelevanceScoringService:
    def __init__(self, llm_provider: BaseLLMProvider, *, top_k: int) -> None:
        self._llm_provider = llm_provider
        self._top_k = top_k

    async def rank(self, query: str, candidates: list[MemoryEntry]) -> list[MemoryMatch]:
        if not candidates:
            return []

        query_embedding = (await self._llm_provider.embed_texts([query]))[0]
        ranked: list[MemoryMatch] = []
        for entry in candidates:
            similarity_score = self._similarity(query_embedding, entry.embedding or [])
            importance_score = float(entry.importance)
            relevance_score = (similarity_score * 0.75) + (importance_score * 0.25)
            ranked.append(
                MemoryMatch(
                    entry=entry,
                    explanation=MemoryRelevanceExplanation(
                        memory_id=entry.id,
                        memory_type=entry.memory_type,
                        similarity_score=similarity_score,
                        importance_score=importance_score,
                        relevance_score=relevance_score,
                        reason=self._reason(entry.memory_type, similarity_score, importance_score),
                    ),
                )
            )
        ranked.sort(key=lambda match: match.explanation.relevance_score, reverse=True)
        return ranked[: self._top_k]

    def _similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sum(a * a for a in left) ** 0.5
        right_norm = sum(b * b for b in right) ** 0.5
        if left_norm == 0 or right_norm == 0:
            return 0.0
        cosine_similarity = dot / (left_norm * right_norm)
        return max(0.0, float(cosine_similarity))

    def _reason(self, memory_type: str, similarity_score: float, importance_score: float) -> str:
        return (
            f"Matched {memory_type} memory with similarity={similarity_score:.3f} "
            f"and importance={importance_score:.3f}"
        )