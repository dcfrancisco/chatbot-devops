from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.runtime import RuntimePlatform
from app.db.session import get_db_session


def get_container(request: Request) -> RuntimePlatform:
    return request.app.state.container


def get_settings(request: Request):
    return request.app.state.settings


async def get_session(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session
