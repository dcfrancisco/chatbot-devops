from app.core.config import Settings
from app.db.session import ping_database
from app.llm.base import BaseLLMProvider


class HealthService:
    def __init__(self, settings: Settings, llm_provider: BaseLLMProvider) -> None:
        self._settings = settings
        self._llm_provider = llm_provider

    async def check(self) -> tuple[str, str]:
        await ping_database()
        await self._llm_provider.healthcheck()
        return self._llm_provider.provider_name, self._llm_provider.chat_model