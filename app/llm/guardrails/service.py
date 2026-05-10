from app.llm.models import LLMChatRequest, LLMChatResponse, LLMEmbeddingRequest


class LLMGuardrailsService:
    def __init__(self, *, max_input_chars: int) -> None:
        self._max_input_chars = max_input_chars

    def validate_chat_request(self, request: LLMChatRequest) -> LLMChatRequest:
        if not request.messages:
            raise ValueError("LLM chat request must include at least one message")
        normalized = [message.model_copy(update={"content": message.content[: self._max_input_chars]}) for message in request.messages]
        return request.model_copy(update={"messages": normalized})

    def validate_embedding_request(self, request: LLMEmbeddingRequest) -> LLMEmbeddingRequest:
        if not request.texts:
            raise ValueError("LLM embedding request must include at least one text")
        return request.model_copy(update={"texts": [text[: self._max_input_chars] for text in request.texts]})

    def validate_chat_response(self, response: LLMChatResponse) -> LLMChatResponse:
        return response.model_copy(update={"text": response.text.strip()})