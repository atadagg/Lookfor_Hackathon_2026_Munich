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
    """Classify the user's request and choose a specialist agent.

    For robustness in the hackathon setting this uses a simple
    keyword-based heuristic that can be upgraded to an OpenAI call
    without changing the public interface.
    """

    messages = state.get("messages", [])
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break

    text = (last_user or "").lower()

    # Very lightweight routing rules derived from the workflow manual.
    if any(k in text for k in ["where is my order", "where's my order", "shipping", "delivery", "tracking"]):
        return RouteDecision(intent="shipping_delay", routed_agent="wismo", confidence=0.7)

    if any(k in text for k in ["missing", "wrong item", "only 2 of the 3", "incorrect item"]):
        return RouteDecision(intent="wrong_or_missing_item", routed_agent="defect", confidence=0.7)

    if any(k in text for k in ["no effect", "did nothing", "still getting bitten", "didn’t help", "didn't help"]):
        return RouteDecision(intent="product_no_effect", routed_agent="defect", confidence=0.6)

    if "refund" in text:
        return RouteDecision(intent="refund_request", routed_agent="defect", confidence=0.6)

    if any(k in text for k in ["cancel", "change address", "update address", "modify order"]):
        return RouteDecision(intent="order_modification", routed_agent="subscription", confidence=0.6)

    if any(k in text for k in ["subscription", "charge", "billed", "pause my monthly"]):
        return RouteDecision(intent="subscription_issue", routed_agent="subscription", confidence=0.6)

    if any(k in text for k in ["discount", "promo code", "coupon", "WELCOME10", "loyalty points"]):
        return RouteDecision(intent="discount_problem", routed_agent="subscription", confidence=0.6)

    if any(k in text for k in ["thank you", "love", "amazing", "saved our trip", "kids love"]):
        return RouteDecision(intent="positive_feedback", routed_agent="wismo", confidence=0.5)

    # Default to shipping so the main vertical slice is always testable.
    return RouteDecision(intent="shipping_delay", routed_agent="wismo", confidence=0.3)


async def route(state: AgentState) -> AgentState:
    """Annotate `AgentState` with routing metadata.

    This will typically be called from `main.py` before handing off to a
    specialist agent graph.
    """

    decision = await classify_intent(state)
    state["intent"] = decision.intent
    state["routed_agent"] = decision.routed_agent
    return state


__all__ = ["RouteDecision", "classify_intent", "route"]
