"""Triage logic for routing conversations to specialist agents.

This module is intentionally lightweight so you can wire in your
preferred LLM + LangGraph stack later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import json

import openai

from core.state import AgentState, Message
from .prompt import INTENT_CLASSIFICATION_PROMPT


@dataclass
class RouteDecision:
    intent: str
    routed_agent: str
    confidence: float


async def classify_intent(state: AgentState) -> RouteDecision:
    """Call OpenAI to classify the user's request.

    This uses the latest conversation messages from `AgentState` and the
    `INTENT_CLASSIFICATION_PROMPT` to select one of the predefined issue
    types and map it to a specialist agent.
    """

    # NOTE: This assumes `openai.api_key` has already been configured
    # at the application boundary (e.g., in `api/server.py`).
    api_key = getattr(openai, "api_key", None)
    if not api_key:
        # Fail closed: if there is no API key, default to shipping/WISMO
        # so the rest of the pipeline still works in local dev.
        return RouteDecision(
            intent="Shipping Delay – Neutral Status Check",
            routed_agent="wismo",
            confidence=0.0,
        )

    openai.api_key = api_key

    messages: List[Message] = state.get("messages", [])  # type: ignore[assignment]
    # Use the last user message as the main query, but pass the recent
    # history for extra context.
    user_texts = [m["content"] for m in messages if m.get("role") == "user"]
    latest_user = user_texts[-1] if user_texts else ""

    history_snippet = "\n\n".join([m["content"] for m in messages[-5:]]) if messages else ""

    system_prompt = INTENT_CLASSIFICATION_PROMPT
    user_prompt = (
        "Latest user message:\n" + latest_user + "\n\n" +
        "Recent conversation snippet (may be empty):\n" + history_snippet
    )

    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception:
        # On any API error, fall back to WISMO so the request still flows.
        return RouteDecision(
            intent="Shipping Delay – Neutral Status Check",
            routed_agent="wismo",
            confidence=0.0,
        )

    raw = resp.choices[0].message["content"]  # type: ignore[index]
    try:
        data: Dict[str, Any] = json.loads(raw)
    except Exception:
        # If the model did not return valid JSON, fall back safely.
        return RouteDecision(
            intent="Shipping Delay – Neutral Status Check",
            routed_agent="wismo",
            confidence=0.0,
        )

    intent = data.get("intent") or "Shipping Delay – Neutral Status Check"
    routed_agent = data.get("routed_agent") or "wismo"
    confidence = float(data.get("confidence") or 0.0)

    return RouteDecision(intent=intent, routed_agent=routed_agent, confidence=confidence)


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
