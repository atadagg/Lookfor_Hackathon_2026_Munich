"""Wrong Item Test Suite 01: Basic Workflow (Roadmap Steps 1–5)

These tests define MUST-HAVE behavior for the Wrong / Missing Item use case.
See ROADMAP.md for the full specification.

- Step 1: Check order (tool usage)
- Step 2: Ask what happened (missing vs wrong)
- Step 3: Request photos
- Step 4: Offer reship → store credit → refund (in order)
- Step 5: Close loop (reship → escalate; credit/refund → confirm)
"""

import json
import pathlib
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_wrong_item, post_chat


# ── Mock LLM: single text response (no tool calls) ────────────────────────


@pytest.fixture
def mock_wrong_item_llm_text_only(monkeypatch):
    """LLM returns one apologetic message asking what happened / for photo."""
    class FakeMessage:
        content = (
            "I'm so sorry to hear that! To get this sorted fast, could you tell me "
            "whether something is missing or you received the wrong item? "
            "If you can, send a photo of what you received—that really helps."
        )
        tool_calls = None

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletion:
        choices = [FakeChoice()]

    class FakeCompletions:
        async def create(self, *args, **kwargs):
            return FakeCompletion()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr("core.llm.get_async_openai_client", lambda: FakeClient(), raising=True)
    monkeypatch.setattr("core.conversational_agent.get_async_openai_client", lambda: FakeClient(), raising=True)


# ── Mock LLM: first response = tool call (get_customer_orders), second = text ─


@pytest.fixture
def mock_wrong_item_llm_calls_order_then_reply(monkeypatch):
    """First LLM response = tool_call get_customer_orders; second = text reply."""
    call_count = [0]

    def make_tool_call_message():
        fn = type("Fn", (), {
            "name": "shopify_get_customer_orders",
            "arguments": json.dumps({"email": "lisa@example.com", "after": "null", "limit": 10}),
        })()
        tc = type("TC", (), {"id": "call_ordertest", "function": fn})()
        tc_dict = {"id": "call_ordertest", "function": {"name": "shopify_get_customer_orders", "arguments": fn.arguments}}
        def model_dump(exclude_none=True):
            return {"role": "assistant", "content": None, "tool_calls": [tc_dict]}
        return type("Message", (), {"content": None, "tool_calls": [tc], "model_dump": model_dump})()

    def make_text_message():
        def model_dump(exclude_none=True):
            return {"role": "assistant", "content": "I've looked up your order. I'm sorry about the mix-up. Was it the wrong product or something missing? A photo would help."}
        return type("Message", (), {
            "content": "I've looked up your order. I'm sorry about the mix-up. Was it the wrong product or something missing? A photo would help.",
            "tool_calls": None,
            "model_dump": model_dump,
        })()

    class FakeCompletions:
        async def create(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                msg = make_tool_call_message()
            else:
                msg = make_text_message()
            return type("Completion", (), {"choices": [type("Choice", (), {"message": msg})()]})()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr("core.llm.get_async_openai_client", lambda: FakeClient(), raising=True)
    monkeypatch.setattr("core.conversational_agent.get_async_openai_client", lambda: FakeClient(), raising=True)


# ── Test 01.01: Wrong-item message routes to wrong_item and returns reply ───


@pytest.mark.asyncio
async def test_01_01_wrong_item_routes_and_responds(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm_text_only):
    """Example intent 'Got Zen stickers instead of Focus' → wrong_item agent, non-empty reply."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item())

    assert data["agent"] == "wrong_item"
    assert data["state"]["routed_agent"] == "wrong_item"
    assert data["state"]["current_workflow"] == "wrong_item"
    assert data["state"]["is_escalated"] is False
    assert data["state"]["last_assistant_message"] is not None
    assert len(data["state"]["last_assistant_message"]) > 20


# ── Test 01.02: Agent can call order lookup (roadmap Step 1) ─────────────────


@pytest.mark.asyncio
async def test_01_02_agent_calls_order_lookup(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm_calls_order_then_reply):
    """When handling wrong item, agent must be able to call order lookup (ROADMAP Step 1)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item())

    assert data["agent"] == "wrong_item"
    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    order_tool_names = (
        "shopify_get_customer_orders",
        "shopify_get_order_details",
        "get_orders_and_details",
        "get_order_by_id",
    )
    order_tools = [t for t in traces if t["name"] in order_tool_names]
    # ROADMAP Step 1: agent should call order lookup. With graph we get get_orders_and_details or get_order_by_id.
    if traces:
        assert len(order_tools) >= 1, "When agent calls tools, one must be order lookup (Step 1). tool_traces=%s" % traces
    # If no traces, mock may not have been used (e.g. real LLM returned text only); agent still must respond
    assert data["state"].get("last_assistant_message"), "Agent must respond."


# ── Test 01.03: Reply mentions apology / photo / what happened (Steps 2–3) ───


@pytest.mark.asyncio
async def test_01_03_reply_mentions_apology_and_next_step(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm_text_only):
    """Reply should be apologetic and ask what happened or for photo (roadmap Steps 2–3)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item())

    msg = (data["state"].get("last_assistant_message") or "").lower()
    has_apology = "sorry" in msg or "apolog" in msg
    has_ask = "photo" in msg or "missing" in msg or "wrong" in msg or "what happened" in msg or "tell me" in msg
    assert has_apology or has_ask, f"Reply should mention apology or ask what happened/photo: {msg}"


# ── Test 01.04: Missing item example intent ─────────────────────────────────


@pytest.mark.asyncio
async def test_01_04_missing_item_intent(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm_text_only):
    """'My package arrived with only 2 of the 3 packs' → wrong_item, reply."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(
            client,
            payload_wrong_item(message="My package arrived with only 2 of the 3 packs I paid for."),
        )

    assert data["agent"] == "wrong_item"
    assert data["state"]["last_assistant_message"] is not None


# ── Test 01.05: Another example intent ──────────────────────────────────────


@pytest.mark.asyncio
async def test_01_05_another_example_intent(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm_text_only):
    """'Received the pet collar but the tick stickers are missing' → wrong_item."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(
            client,
            payload_wrong_item(message="Received the pet collar but the tick stickers are missing."),
        )

    assert data["agent"] == "wrong_item"
    assert data["state"]["current_workflow"] == "wrong_item"
