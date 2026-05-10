from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies import get_container
from app.core.container import ServiceContainer
from app.models.api import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck(container: ServiceContainer = Depends(get_container)) -> HealthResponse:
    provider, chat_model = await container.health_service.check()
    return HealthResponse(
        status="ok",
        database="ok",
        llm_provider=provider,
        llm_model=chat_model,
        embedding_model=container.settings.llm_embedding_model,
        tools=len(container.tool_registry.list()),
    )

