from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.llm import LLMMessage


class LLMChatRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMChatResponse(BaseModel):
    provider_name: str
    model: str
    text: str
    finish_reason: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMEmbeddingRequest(BaseModel):
    texts: list[str]
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMEmbeddingResponse(BaseModel):
    provider_name: str
    model: str
    embeddings: list[list[float]]
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMRouteDecision(BaseModel):
    capability: str
    provider_name: str
    model: str
    fallback_index: int = 0
    reason: str
    attempted_providers: list[str] = Field(default_factory=list)