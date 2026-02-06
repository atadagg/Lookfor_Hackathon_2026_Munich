"""Triage logic for routing conversations to specialist agents.

This module is intentionally lightweight so you can wire in your
preferred LLM + LangGraph stack later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.state import AgentState
from .prompt import INTENT_CLASSIFICATION_PROMPT


@dataclass
class RouteDecision:
    intent: str
    routed_agent: str
    confidence: float


async def classify_intent(state: AgentState) -> RouteDecision:
    """Call your LLM of choice to classify the user's request.

    For now this is a stub that always returns `wismo` so the rest of the
    pipeline can be tested without a model.
    """

    # TODO: Replace with real LLM call using `INTENT_CLASSIFICATION_PROMPT`.
    return RouteDecision(intent="shipping_issue", routed_agent="wismo", confidence=0.5)


async def route(state: AgentState) -> AgentState:
    """Annotate `AgentState` with routing metadata.

    This will typically be called from `main.py` before handing off to a
    specialist agent graph.
    """

    decision = await classify_intent(state)
    state.intent = decision.intent
    state.routed_agent = decision.routed_agent
    return state


__all__ = ["RouteDecision", "classify_intent", "route"]
