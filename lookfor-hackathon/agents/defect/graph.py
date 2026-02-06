"""Graph for defective / wrong / missing item resolution."""

from __future__ import annotations

from typing import Any

from core.base_agent import BaseAgent
from core.state import AgentState


class DefectAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="defect")

    def build_graph(self) -> Any:
        """Return the internal graph / workflow object.

        TODO: Implement photo request → reship / refund logic.
        """

        return None

    async def handle(self, state: AgentState) -> AgentState:
        """Handle a defect conversation turn (stub)."""

        state.slots.setdefault("defect", {})["handled"] = True
        return state


__all__ = ["DefectAgent"]
