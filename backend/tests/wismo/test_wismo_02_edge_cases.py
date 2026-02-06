"""WISMO Test Suite 02: Edge Cases - Missing Data, Malformed Inputs

Covers edge cases that could break during demo:
- Missing customer email
- Missing first_name/last_name
- Empty messages
- Very long messages
- Special characters in order IDs
- Various order ID formats (#123, NP12345, order 123, etc.)
- Unicode characters
- Email format edge cases
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


# ── Test 02.01: Missing customer email → escalates ──────────────────────


@pytest.mark.asyncio
async def test_02_01_missing_email_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Empty customer_email → immediate escalation."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    assert "monica" in data["state"]["last_assistant_message"].lower() or "looping" in data["state"]["last_assistant_message"].lower()


# ── Test 02.02: Missing first_name handled gracefully ───────────────────


@pytest.mark.asyncio
async def test_02_02_missing_first_name_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Missing first_name should not crash."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(first_name=""))

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.03: Missing last_name handled gracefully ────────────────────


@pytest.mark.asyncio
async def test_02_03_missing_last_name_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Missing last_name should not crash."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(last_name=""))

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.04: Empty message handled ─────────────────────────────────────


@pytest.mark.asyncio
async def test_02_04_empty_message_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Empty message should not crash."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message=""))

    # Should either route correctly or escalate, but not crash
    assert data["agent"] in ("wismo", "escalated")


# ── Test 02.05: Very long message handled ────────────────────────────────


@pytest.mark.asyncio
async def test_02_05_very_long_message_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Very long message (10KB) should not crash."""
    from api.server import app

    long_msg = "Where is my order? " * 500  # ~10KB
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message=long_msg))

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.06: Order ID format #12345 ───────────────────────────────────


@pytest.mark.asyncio
async def test_02_06_order_id_format_hash_number(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Order ID format: #12345 should be extracted."""
    from api.server import app

    conv_id = f"wismo-hash-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Where is my order?"})
        data = await _post_chat(client, {**base, "message": "It's #12345"})

    assert data["state"]["workflow_step"] == "wait_promise_set"
    traces = data["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["inputs"]["order_id"] == "#12345"


# ── Test 02.07: Order ID format NP12345 ───────────────────────────────────


@pytest.mark.asyncio
async def test_02_07_order_id_format_np_number(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Order ID format: NP12345 should be extracted."""
    from api.server import app

    conv_id = f"wismo-np-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Where is my order?"})
        data = await _post_chat(client, {**base, "message": "It's NP12345"})

    assert data["state"]["workflow_step"] == "wait_promise_set"
    traces = data["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["inputs"]["order_id"] == "#12345"  # NP prefix stripped


# ── Test 02.08: Order ID format "order 123" ───────────────────────────────


@pytest.mark.asyncio
async def test_02_08_order_id_format_order_word(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Order ID format: 'order 123' should be extracted."""
    from api.server import app

    conv_id = f"wismo-word-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Where is my order?"})
        data = await _post_chat(client, {**base, "message": "It's order 123"})

    assert data["state"]["workflow_step"] == "wait_promise_set"
    traces = data["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["inputs"]["order_id"] == "#123"


# ── Test 02.09: Order ID format bare number ────────────────────────────────


@pytest.mark.asyncio
async def test_02_09_order_id_format_bare_number(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Order ID format: bare number '43189' should be extracted (when message is just the number)."""
    from api.server import app

    conv_id = f"wismo-bare-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Where is my order?"})
        # extract_order_id only matches bare numbers if entire message is the number
        data = await _post_chat(client, {**base, "message": "43189"})

    assert data["state"]["workflow_step"] == "wait_promise_set"
    traces = data["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["inputs"]["order_id"] == "#43189"


# ── Test 02.10: Unicode characters in message ────────────────────────────


@pytest.mark.asyncio
async def test_02_10_unicode_characters_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Unicode characters (emojis, accents) should not break processing."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Where is my order? 😊 Ça va? Café résumé")
        )

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.11: Email with plus sign ──────────────────────────────────────


@pytest.mark.asyncio
async def test_02_11_email_plus_sign_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Email with + sign (e.g., user+tag@example.com) should work."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(email="user+tag@example.com", message="Where is my order?")
        )

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.12: Email with subdomain ──────────────────────────────────────


@pytest.mark.asyncio
async def test_02_12_email_subdomain_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Email with subdomain should work."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(email="user@mail.example.com", message="Where is my order?")
        )

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False


# ── Test 02.13: Missing shopify_customer_id handled ───────────────────────


@pytest.mark.asyncio
async def test_02_13_missing_shopify_customer_id_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Missing shopify_customer_id should not crash."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(shopify_customer_id="", message="Where is my order?")
        )

    assert data["agent"] == "wismo"
    assert data["state"]["is_escalated"] is False
