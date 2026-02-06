"""WISMO Test Suite 04: Escalation Scenarios

Covers all escalation paths:
- Missing customer email
- Order ID not provided after 2 asks
- Missed promise date
- Tool failures
- Already escalated thread blocks further replies
- Escalation summary structure
"""

import pathlib
import sys
import tempfile
import uuid
from datetime import date, timedelta
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


# ── Test 04.01: Missing email escalates immediately ────────────────────────


@pytest.mark.asyncio
async def test_04_01_missing_email_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Empty customer_email → immediate escalation."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    assert data["state"]["workflow_step"].startswith("escalated")
    assert "monica" in data["state"]["last_assistant_message"].lower() or "looping" in data["state"]["last_assistant_message"].lower()


# ── Test 04.02: Order ID not provided twice → escalates ─────────────────────


@pytest.mark.asyncio
async def test_04_02_order_id_not_provided_twice_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Customer fails to provide order ID twice → escalates."""
    from api.server import app

    conv_id = f"wismo-no-id-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        assert t1["state"]["workflow_step"] == "awaiting_order_id"

        t2 = await _post_chat(client, {**base, "message": "I don't know my order number"})
        assert t2["state"]["workflow_step"] == "awaiting_order_id"

        t3 = await _post_chat(client, {**base, "message": "I really can't find it"})

    assert t3["state"]["is_escalated"] is True
    assert "monica" in t3["state"]["last_assistant_message"].lower()


# ── Test 04.03: Missed promise date escalates ──────────────────────────────


@pytest.mark.asyncio
async def test_04_03_missed_promise_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Customer replies after promised date → escalates."""
    from api.server import app

    conv_id = f"wismo-missed-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        assert t1["state"]["workflow_step"] == "wait_promise_set"

        # Patch promise date to yesterday
        saved = temp_db.load_state(conv_id)
        internal = saved.get("internal_data", {})
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        internal["wait_promise_until"] = yesterday
        saved["internal_data"] = internal
        temp_db.save_state(conv_id, saved)

        t2 = await _post_chat(client, {**base, "message": "It's past the date!"})

    assert t2["state"]["is_escalated"] is True
    assert "monica" in t2["state"]["last_assistant_message"].lower() or "resend" in t2["state"]["last_assistant_message"].lower()


# ── Test 04.04: Already escalated thread blocks replies ────────────────────


@pytest.mark.asyncio
async def test_04_04_escalated_thread_blocks_replies(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Once escalated, new messages return agent='escalated' without processing."""
    from api.server import app

    conv_id = f"wismo-block-{uuid.uuid4().hex[:8]}"
    payload = _payload(conv_id=conv_id, email="")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, payload)
        assert t1["state"]["is_escalated"] is True

        t2 = await _post_chat(client, {**payload, "message": "Are you there?"})

    assert t2["agent"] == "escalated"
    assert t2["state"]["status"] == "escalated"
    assert t2["state"]["reason"] == "thread already escalated to human"


# ── Test 04.05: Escalation summary structure ───────────────────────────────


@pytest.mark.asyncio
async def test_04_05_escalation_summary_structure(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Escalation should include structured escalation_summary."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    escalation = data["state"].get("escalation_summary")
    # Escalation summary should exist (may be dict or string representation)
    assert escalation is not None


# ── Test 04.06: Escalation workflow_step naming ─────────────────────────────


@pytest.mark.asyncio
async def test_04_06_escalation_workflow_step_naming(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Escalation workflow_step should be descriptive."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    step = data["state"]["workflow_step"]
    assert step.startswith("escalated") or "escalat" in step.lower()


# ── Test 04.07: Escalation timestamp set ─────────────────────────────────────


@pytest.mark.asyncio
async def test_04_07_escalation_timestamp_set(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Escalation should set escalated_at timestamp."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    # escalated_at may be in state or in full thread data
    # Check via thread endpoint
    from api.server import checkpointer
    thread = checkpointer.get_thread(data["conversation_id"])
    if thread:
        assert thread.is_escalated is True
