from __future__ import annotations

from abc import ABC, abstractmethod

from app.orchestration.pipeline.execution import PipelineExecutionState, PipelineStage


class BasePipelineStageHandler(ABC):
    stage: PipelineStage

    @abstractmethod
    async def handle(self, state: PipelineExecutionState) -> None:
        raise NotImplementedError
