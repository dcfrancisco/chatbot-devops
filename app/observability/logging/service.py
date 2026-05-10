from __future__ import annotations

from typing import Any

from app.core.logging import get_logger


class StructuredLoggingService:
    def __init__(self, name: str = "app.observability") -> None:
        self._logger = get_logger(name)

    def info(self, event: str, **metadata: Any) -> None:
        self._logger.info(event, extra=metadata)

    def warning(self, event: str, **metadata: Any) -> None:
        self._logger.warning(event, extra=metadata)

    def exception(self, event: str, **metadata: Any) -> None:
        self._logger.exception(event, extra=metadata)