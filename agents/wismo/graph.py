"""Internal micro-state machine for WISMO.

Wire this up to LangGraph during implementation; for now we use a
minimal callable to keep the surface area small.
"""

from __future__ import annotations

from typing import Any

from core.base_agent import BaseAgent
from core.state import AgentState
from agents.shipping.graph import build_shipping_graph


class WismoAgent(BaseAgent):
    """Specialist agent for Shipping Delay / WISMO workflows.

    Internally this delegates to the compiled LangGraph defined in
    `agents.shipping.graph.build_shipping_graph`.
    """

    def __init__(self) -> None:
        super().__init__(name="wismo")
        # Lazily compiled graph application.
        self._app: Any | None = None

    def build_graph(self) -> Any:
        """Return (and cache) the internal graph / workflow object."""

        if self._app is None:
            self._app = build_shipping_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        """Handle a WISMO conversation turn via the shipping graph."""

        # Make sure the workflow metadata is set for observability.
        state["current_workflow"] = "shipping"

        app = self.build_graph()

        # Prefer async execution if available.
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)

        # Fallback to sync invoke in a minimal way.
        return app.invoke(state)


__all__ = ["WismoAgent"]
