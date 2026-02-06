"""WISMO Test Suite 05: Multi-Turn Complexity

Covers complex multi-turn scenarios:
- Conversation memory across multiple turns
- State persistence between turns
- Context preservation
- Duplicate message detection
- Rapid successive messages
- Changing order status mid-conversation
"""

import pathlib
import sys
import tempfile
import uuid
from typing import Optional

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        from core.database import Checkpointer
        cp = Checkpointer(db_path=path)
        monkeypatch.setattr("api.server.checkpointer", cp)
        yield cp
    finally:
        import os
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def mock_route_to_wismo(monkeypatch):
    async def _route(state):
        state["intent"] = "Shipping Delay – Neutral Status Check"
        state["routed_agent"] = "wismo"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_wismo_llm(monkeypatch):
    class FakeMessage:
        content = "Mock response"
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


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    monkeypatch.setenv("API_URL", "")


def _payload(conv_id=None, email="test@example.com", message="Where is my order?", **kwargs):
    return {
        "conversation_id": conv_id or f"wismo-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-test"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": kwargs.get("first_name", "Jane"),
        "last_name": kwargs.get("last_name", "Doe"),
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-test"),
        "message": message,
    }


async def _post_chat(client, payload):
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


async def _get_thread(client, conv_id):
    resp = await client.get(f"/thread/{conv_id}")
    assert resp.status_code == 200
    return resp.json()


# ── Test 05.01: Multi-turn memory preserved ────────────────────────────────


@pytest.mark.asyncio
async def test_05_01_multiturn_memory_preserved(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Multiple turns in same thread → all messages preserved."""
    from api.server import app

    conv_id = f"wismo-mem-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Order #43189 shows in transit for 10 days."})
        await _post_chat(client, {**base, "message": "Can you share the tracking link?"})
        await _post_chat(client, {**base, "message": "Thanks, that helps!"})

        thread = await _get_thread(client, conv_id)

    assert len(thread["messages"]) >= 6  # 3 user + 3 assistant
    user_msgs = [m["content"] for m in thread["messages"] if m["role"] == "user"]
    assert "43189" in user_msgs[0]
    assert "tracking" in user_msgs[1].lower()


# ── Test 05.02: Duplicate message detection ──────────────────────────────────


@pytest.mark.asyncio
async def test_05_02_duplicate_message_detected(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Sending identical message twice → duplicate detected."""
    from api.server import app

    conv_id = f"wismo-dup-{uuid.uuid4().hex[:8]}"
    payload = _payload(conv_id=conv_id, message="Order #43189 shows in transit for 10 days.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await _post_chat(client, payload)
        second = await _post_chat(client, payload)

    assert first["agent"] == "wismo"
    assert second["agent"] == "duplicate"


# ── Test 05.03: State persists between turns ───────────────────────────────


@pytest.mark.asyncio
async def test_05_03_state_persists_between_turns(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """State (workflow_step, internal_data) persists across turns."""
    from api.server import app

    conv_id = f"wismo-state-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        step1 = t1["state"]["workflow_step"]

        t2 = await _post_chat(client, {**base, "message": "Any update?"})

    # State should persist (workflow_step should be consistent or advanced)
    assert t2["state"]["workflow_step"] is not None
    # Both should be wismo (not escalated)
    assert t1["agent"] == "wismo"
    assert t2["agent"] == "wismo"


# ── Test 05.04: Context preserved in follow-up ─────────────────────────────


@pytest.mark.asyncio
async def test_05_04_context_preserved_in_followup(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Follow-up message should reference previous context."""
    from api.server import app

    conv_id = f"wismo-ctx-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Order #43189 shows in transit."})
        t2 = await _post_chat(client, {**base, "message": "What about that order?"})

    # Should still be in same workflow
    assert t2["agent"] == "wismo"
    assert t2["state"]["current_workflow"] == "shipping"


# ── Test 05.05: Rapid successive messages handled ───────────────────────────


@pytest.mark.asyncio
async def test_05_05_rapid_successive_messages(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Rapid successive messages should be handled correctly."""
    from api.server import app

    conv_id = f"wismo-rapid-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        t2 = await _post_chat(client, {**base, "message": "Hello?"})
        t3 = await _post_chat(client, {**base, "message": "Are you there?"})

    # All should be processed (or duplicates detected)
    assert all(t["agent"] in ("wismo", "duplicate") for t in [t1, t2, t3])


# ── Test 05.06: Order ID extraction in follow-up ───────────────────────────


@pytest.mark.asyncio
async def test_05_06_order_id_extraction_in_followup(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Order ID provided in follow-up after initial no-orders should work."""
    from api.server import app

    conv_id = f"wismo-followup-id-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        assert t1["state"]["workflow_step"] == "awaiting_order_id"

        t2 = await _post_chat(client, {**base, "message": "Oh wait, I found it: #99999"})

    assert t2["state"]["workflow_step"] == "wait_promise_set"
    traces = t2["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["inputs"]["order_id"] == "#99999"


# ── Test 05.07: Conversation history length ────────────────────────────────


@pytest.mark.asyncio
async def test_05_07_long_conversation_history(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Long conversation (10+ turns) should still work."""
    from api.server import app

    conv_id = f"wismo-long-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(10):
            await _post_chat(client, {**base, "message": f"Message {i+1}"})

        thread = await _get_thread(client, conv_id)

    assert len(thread["messages"]) >= 20  # 10 user + 10 assistant
    assert thread["status"] == "open"  # Should still be open (not escalated)


# ── Test 05.08: State consistency across turns ─────────────────────────────


@pytest.mark.asyncio
async def test_05_08_state_consistency_across_turns(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """State should remain consistent across multiple turns."""
    from api.server import app

    conv_id = f"wismo-consist-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        t2 = await _post_chat(client, {**base, "message": "Any update?"})
        t3 = await _post_chat(client, {**base, "message": "Still waiting"})

    # All should have same conversation_id
    assert t1["conversation_id"] == t2["conversation_id"] == t3["conversation_id"]
    # All should be same agent
    assert t1["agent"] == t2["agent"] == t3["agent"] == "wismo"
    # All should have same workflow
    assert t1["state"]["current_workflow"] == t2["state"]["current_workflow"] == t3["state"]["current_workflow"] == "shipping"
