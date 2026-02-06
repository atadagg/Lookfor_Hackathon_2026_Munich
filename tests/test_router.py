import asyncio
import pathlib
import sys

# Ensure the project root is on sys.path so `router` and `core` are importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from router.logic import classify_intent, RouteDecision
from core.state import AgentState, Message


async def _run_classify_without_api_key() -> RouteDecision:
    # Minimal state with a single user message
    state = AgentState(messages=[Message(role="user", content="Where is my order?")])
    decision = await classify_intent(state)
    return decision


def test_classify_intent_falls_back_without_api_key(monkeypatch):
    """When no OpenAI API key is configured, we fall back to WISMO.

    This ensures the router still behaves predictably in local/dev
    environments or CI where no LLM credentials are present.
    """

    # Ensure there is no API key configured on the openai module.
    import openai

    if hasattr(openai, "api_key"):
        monkeypatch.delattr(openai, "api_key", raising=False)

    decision = asyncio.run(_run_classify_without_api_key())

    assert decision.routed_agent == "wismo"
    assert decision.intent.startswith("Shipping Delay")
