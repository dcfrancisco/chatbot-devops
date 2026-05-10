from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_container, get_session
from app.core.container import ServiceContainer
from app.models.api import ToolDescriptor, ToolExecutionRequest, ToolExecutionResponse
from app.tools.registry import ToolNotFoundError

router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=list[ToolDescriptor])
async def list_tools(container: ServiceContainer = Depends(get_container)) -> list[ToolDescriptor]:
    return container.tool_execution_service.list_tools()


@router.get("/tools/{tool_name}", response_model=ToolDescriptor)
async def get_tool(tool_name: str, container: ServiceContainer = Depends(get_container)) -> ToolDescriptor:
    try:
        return container.tool_execution_service.get_tool(tool_name)
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/tools/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    container: ServiceContainer = Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> ToolExecutionResponse:
    return await container.tool_execution_service.execute(session, request)
