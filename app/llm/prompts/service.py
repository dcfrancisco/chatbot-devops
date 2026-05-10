from app.llm.models import LLMChatRequest
from app.models.llm import LLMMessage


class PromptAssemblyFlow:
    def build_chat_request(
        self,
        *,
        messages: list[LLMMessage],
        model: str | None,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, object] | None = None,
    ) -> LLMChatRequest:
        return LLMChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata or {},
        )