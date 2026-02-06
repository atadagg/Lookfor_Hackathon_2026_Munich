import asyncio
import pathlib
import sys

# Ensure the project root is on sys.path so `router` and `core` are importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from router.logic import classify_intent, RouteDecision
from core.state import AgentState, Message


async def _run_classify_with_error() -> tuple[RouteDecision, AgentState]:
    # Minimal state with a single user message
    state = AgentState(messages=[Message(role="user", content="Where is my order?")])
    decision = await classify_intent(state)
    return decision, state


def test_classify_intent_escalates_on_llm_error(monkeypatch):
    """If the LLM call fails, the thread should be escalated, not auto-routed."""

    import openai

    async def fake_acreate(*args, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(openai.ChatCompletion, "acreate", fake_acreate, raising=True)

    decision, state = asyncio.run(_run_classify_with_error())

    assert decision.intent.startswith("Escalated")
    assert "LLM" in decision.intent
    assert decision.routed_agent == ""
    assert state.get("is_escalated") is True
    internal = state.get("internal_data") or {}
    summary = internal.get("escalation_summary") or {}
    assert summary.get("reason") == "llm_error"
    assert "LLM down" in summary.get("details", {}).get("error", "")
