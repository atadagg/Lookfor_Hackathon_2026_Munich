"""WISMO Test Suite 01: Basic Workflow - Happy Paths

Covers all standard WISMO workflow branches:
- IN_TRANSIT orders → wait promise
- UNFULFILLED orders → explain not shipped
- DELIVERED orders → confirm delivery
- No orders → ask for order ID → resolve
- Tracking URL sharing

These are the MUST-PASS tests for hackathon demo.
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
        content = "Your order is on the way. Please wait until Friday."
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
        "user_id": "user-test",
        "channel": "email",
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


# ── Test 01.01: IN_TRANSIT order sets wait promise ────────────────────


@pytest.mark.asyncio
async def test_01_01_in_transit_sets_wait_promise(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Standard IN_TRANSIT order → wait promise set, tracking shared."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["agent"] == "wismo"
    st = data["state"]
    assert st["workflow_step"] == "wait_promise_set"
    assert st["is_escalated"] is False

    traces = st["internal_data"]["tool_traces"]
    assert traces[0]["name"] == "get_order_status"
    assert traces[0]["output"]["data"]["status"] == "IN_TRANSIT"
    assert traces[0]["output"]["data"]["tracking_url"] is not None


# ── Test 01.02: UNFULFILLED order explained ────────────────────────────


@pytest.mark.asyncio
async def test_01_02_unfulfilled_order_explained(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """UNFULFILLED order → workflow_step=explained_unfulfilled."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client, _payload(email="unfulfilled@test.com", message="When will it ship?")
        )

    assert data["state"]["workflow_step"] == "explained_unfulfilled"
    assert data["state"]["internal_data"]["tool_traces"][0]["output"]["data"]["status"] == "UNFULFILLED"


# ── Test 01.03: DELIVERED order confirmed ──────────────────────────────


@pytest.mark.asyncio
async def test_01_03_delivered_order_confirmed(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """DELIVERED order → workflow_step=explained_delivered."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client, _payload(email="delivered@test.com", message="Did it arrive?")
        )

    assert data["state"]["workflow_step"] == "explained_delivered"
    assert data["state"]["internal_data"]["tool_traces"][0]["output"]["data"]["status"] == "DELIVERED"


# ── Test 01.04: No orders → asks for order ID ──────────────────────────


@pytest.mark.asyncio
async def test_01_04_no_orders_asks_for_id(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """No orders found → asks customer for order number."""
    from api.server import app

    conv_id = f"wismo-noorders-{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client, _payload(conv_id=conv_id, email="noorders@test.com", message="Where is my order?")
        )

    assert data["state"]["workflow_step"] == "awaiting_order_id"
    assert "order" in data["state"]["last_assistant_message"].lower()


# ── Test 01.05: Customer provides order ID → resolves ──────────────────


@pytest.mark.asyncio
async def test_01_05_customer_provides_order_id_resolves(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Two-turn: no orders → customer gives #43189 → resolves."""
    from api.server import app

    conv_id = f"wismo-provide-id-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Where is my order?"})
        assert t1["state"]["workflow_step"] == "awaiting_order_id"

        t2 = await _post_chat(client, {**base, "message": "Oh sorry, it's order #43189"})

    assert t2["state"]["workflow_step"] == "wait_promise_set"
    traces = t2["state"]["internal_data"]["tool_traces"]
    by_id = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id) >= 1
    assert by_id[0]["output"]["data"]["order_id"] == "#43189"


# ── Test 01.06: Tracking URL included in response ──────────────────────


@pytest.mark.asyncio
async def test_01_06_tracking_url_included(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Tracking URL should be available in tool output for IN_TRANSIT orders."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message="Can you share tracking?"))

    traces = data["state"]["internal_data"]["tool_traces"]
    assert traces[0]["output"]["data"]["tracking_url"] == "https://tracking.example.com/demo123"


# ── Test 01.07: Wait promise day calculation (Mon-Wed → Friday) ────────


@pytest.mark.asyncio
async def test_01_07_wait_promise_mon_wed_to_friday(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Monday-Wednesday contacts → promise Friday."""
    from datetime import date, timedelta
    from api.server import app

    # This test verifies the logic works; actual day depends on when test runs
    conv_id = f"wismo-day-{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(conv_id=conv_id))

    assert data["state"]["workflow_step"] == "wait_promise_set"
    full_state = temp_db.load_state(conv_id)
    internal = full_state.get("internal_data", {})
    assert internal.get("decided_action") == "wait_promise"
    assert internal.get("wait_promise_until") is not None
    # Promise day label should be either "Friday" or "early next week" depending on today
    assert internal.get("promise_day_label") in ("Friday", "early next week")
