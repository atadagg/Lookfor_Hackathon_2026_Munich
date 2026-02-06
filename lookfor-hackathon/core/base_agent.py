"""Abstract base class for all customer support agents.

This defines the common interface that specialist agents (wismo, defect,
subscription, etc.) must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .state import AgentState


class BaseAgent(ABC):
    """Base class for all agents.

    Concrete agents should implement `build_graph` and `handle`.
    `handle` can either run the internal graph or delegate to LangGraph
    execution depending on how you wire things up later.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def build_graph(self) -> Any:
        """Return the internal LangGraph / state machine object.

        For now this returns `Any` so you can plug in LangGraph later
        without changing the interface.
        """

    @abstractmethod
    async def handle(self, state: AgentState) -> AgentState:
        """Run the agent for a single step / turn.

        This method should be invoked by `main.py` or the router once the
        conversation has been triaged to this specialist.
        """


__all__ = ["BaseAgent"]
