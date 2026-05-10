from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.container import build_container
from app.core.logging import configure_logging, get_logger
from app.observability.tracing.middleware import TraceContextMiddleware


@asynccontextmanager
async def lifespan(_application: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    _application.state.settings = settings
    _application.state.container = build_container(settings)
    logger = get_logger(__name__)
    logger.info("application_startup")
    yield
    await _application.state.container.aclose()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.add_middleware(TraceContextMiddleware)
    application.include_router(api_router)
    return application



app = create_app()
