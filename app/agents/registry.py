from typing import Any

from app.agents.base import BaseAgent
from app.shared.registry import NamedRegistry


class AgentRegistry(NamedRegistry[BaseAgent[Any, Any]]):
    pass