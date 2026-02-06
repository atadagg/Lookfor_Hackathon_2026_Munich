"""Internal micro-state machine for WISMO.

Wire this up to LangGraph during implementation; for now we use a
minimal callable to keep the surface area small.
"""

from __future__ import annotations

from typing import Any

from core.base_agent import BaseAgent
from core.state import AgentState


class WismoAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="wismo")

    def build_graph(self) -> Any:
        """Return the internal graph / workflow object.

        TODO: Replace with a real LangGraph graph definition.
        """

        return None

    async def handle(self, state: AgentState) -> AgentState:
        """Handle a WISMO conversation turn.

        This is a stub so the router → agent interface is testable.
        """

        state.slots.setdefault("wismo", {})["handled"] = True
        return state


__all__ = ["WismoAgent"]
