"""Graph for subscription flows: Skip → Discount → Cancel logic."""

from __future__ import annotations

from typing import Any

from core.base_agent import BaseAgent
from core.state import AgentState


class SubscriptionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="subscription")

    def build_graph(self) -> Any:
        """Return the internal graph / workflow object.

        TODO: Implement LangGraph for skip/discount/cancel flow.
        """

        return None

    async def handle(self, state: AgentState) -> AgentState:
        """Handle a subscription conversation turn (stub)."""

        state.slots.setdefault("subscription", {})["handled"] = True
        return state


__all__ = ["SubscriptionAgent"]
