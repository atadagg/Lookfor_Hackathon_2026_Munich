"""Triage logic for routing conversations to specialist agents.

This module is intentionally lightweight so you can wire in your
preferred LLM + LangGraph stack later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import os

from openai import AsyncOpenAI

from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .prompt import INTENT_CLASSIFICATION_PROMPT


@dataclass
class RouteDecision:
    intent: str
    routed_agent: str
    confidence: float


# Lazily created async OpenAI client; avoids import-time failures in
# environments (like tests) where OPENAI_API_KEY is not set.
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Let the caller handle this as an LLM error.
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


def _escalate_due_to_llm_error(state: AgentState, error: str | None = None) -> RouteDecision:
    """Mark the thread as escalated when routing LLMs fail.

    This ensures we do not silently fall back to automation when the LLM
    is unavailable or misbehaves. Instead, we set a clear escalation
    summary and add a user-facing assistant message.
    """

    internal = state.get("internal_data") or {}
    internal["escalation_summary"] = EscalationSummary(
        reason="llm_error",
        details={"error": error or "unknown"},
    ).model_dump()
    state["internal_data"] = internal

    state["is_escalated"] = True
    state["escalated_at"] = datetime.utcnow()

    messages = list(state.get("messages", []))
    messages.append(
        Message(
            role="assistant",
            content=(
                "I'm having trouble routing your request automatically right now. "
                "To make sure you get the right support, I'm looping in Monica, "
                "our Head of CS, who will take it from here."
            ),
        )
    )
    state["messages"] = messages
    state["workflow_step"] = "escalated_llm_error"

    # No specialist agent should be invoked after this point.
    return RouteDecision(
        intent="Escalated – LLM Error",
        routed_agent="",
        confidence=0.0,
    )


async def classify_intent(state: AgentState) -> RouteDecision:
    """Call OpenAI to classify the user's request.

    This uses the latest conversation messages from `AgentState` and the
    `INTENT_CLASSIFICATION_PROMPT` to select one of the predefined issue
    types and map it to a specialist agent.
    """

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
        client = _get_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        # Any LLM error (including missing API key) should escalate the
        # thread rather than falling back silently to automation.
        return _escalate_due_to_llm_error(state, str(exc))

    raw = resp.choices[0].message.content or ""
    try:
        data: Dict[str, Any] = json.loads(raw)
    except Exception as exc:
        # If the model did not return valid JSON, escalate rather than
        # guessing a route.
        return _escalate_due_to_llm_error(state, f"invalid_json: {exc}")

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
    state["intent"] = decision.intent
    state["routed_agent"] = decision.routed_agent
    return state


__all__ = ["RouteDecision", "classify_intent", "route", "_get_client"]
