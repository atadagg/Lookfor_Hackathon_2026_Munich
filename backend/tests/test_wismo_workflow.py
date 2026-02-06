"""Comprehensive WISMO workflow tests.

Covers every branch of the Shipping Delay – Neutral Status Check workflow:

  1. IN_TRANSIT order  → wait promise set, tracking shared
  2. UNFULFILLED order → told "not shipped yet"
  3. DELIVERED order   → told "marked delivered"
  4. No orders found   → asks for order ID
  5. No orders → customer provides order ID → resolves
  6. No orders → customer provides no ID twice → escalates
  7. Missing customer email → escalates
  8. Duplicate message detection
  9. Multi-turn continuity (memory preserved)
 10. Escalation after missed promise date (missed promise)
 11. Escalation blocks further auto-replies
 12. Wait-promise day logic (Mon-Wed → Friday, Thu-Sun → early next week)
 13. Tracking URL shared when in transit

Run with:  pytest tests/test_wismo_workflow.py -v
"""

import pathlib
import sys
import tempfile
import uuid
from datetime import date, timedelta
from typing import Optional

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Shared fixtures ──────────────────────────────────────────────────


@pytest.fixture
def temp_db(monkeypatch):
    """Isolated temp SQLite DB for each test."""
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
    """Bypass real LLM router → always route to wismo."""

    async def _route(state):
        state["intent"] = "Shipping Delay – Neutral Status Check"
        state["routed_agent"] = "wismo"
        return state

    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_wismo_llm(monkeypatch):
    """Mock the LLM in generate_response so tests don't need API keys."""

    class FakeMessage:
        content = "Mock response from customer support."

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

    monkeypatch.setattr(
        "core.llm.get_async_openai_client", lambda: FakeClient(), raising=True
    )


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    """Force mock tool path (no real Shopify/Skio calls)."""
    monkeypatch.setenv("API_URL", "")


def _payload(
    conv_id: Optional[str] = None,
    email: str = "test@example.com",
    message: str = "Where is my order?",
    first_name: str = "Jane",
    last_name: str = "Doe",
) -> dict:
    return {
        "conversation_id": conv_id or "wismo-%s" % uuid.uuid4().hex[:8],
        "user_id": "user-test",
        "channel": "email",
        "customer_email": email,
        "first_name": first_name,
        "last_name": last_name,
        "shopify_customer_id": "cust-test",
        "message": message,
    }


async def _post_chat(client: AsyncClient, payload: dict) -> dict:
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, "Expected 200, got %d: %s" % (resp.status_code, resp.text)
    return resp.json()


async def _get_thread(client: AsyncClient, conv_id: str) -> dict:
    resp = await client.get("/thread/%s" % conv_id)
    assert resp.status_code == 200
    return resp.json()


def _extract_tool_output(tool_traces, tool_name, index=0):
    """Extract a specific tool's output data from tool_traces."""
    matches = [t for t in tool_traces if t["name"] == tool_name]
    if index < len(matches):
        return matches[index].get("output", {}).get("data", {})
    return {}


# ── Test 1: IN_TRANSIT order → wait promise + tracking ───────────────


@pytest.mark.asyncio
async def test_wismo_in_transit_wait_promise(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Default mock email → IN_TRANSIT order.

    Expected: routed to wismo, workflow=shipping, not escalated,
    tool traces show IN_TRANSIT, wait_promise_set step, and a response sent.
    """
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["agent"] == "wismo"
    st = data["state"]
    assert st["routed_agent"] == "wismo"
    assert st["current_workflow"] == "shipping"
    assert st["is_escalated"] is False
    assert st["last_assistant_message"] is not None

    # Tool traces should have get_order_status call with IN_TRANSIT
    traces = st.get("internal_data", {}).get("tool_traces", [])
    assert len(traces) >= 1
    assert traces[0]["name"] == "get_order_status"
    assert traces[0]["output"]["success"] is True
    order_data = traces[0]["output"]["data"]
    assert order_data["status"] == "IN_TRANSIT"
    assert order_data["order_id"] == "#1001"
    assert order_data["tracking_url"] is not None

    # Workflow step should be wait_promise_set
    assert st["workflow_step"] == "wait_promise_set"


# ── Test 2: UNFULFILLED order → told not shipped yet ──────────────────


@pytest.mark.asyncio
async def test_wismo_unfulfilled_order(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Email unfulfilled@test.com → UNFULFILLED mock scenario.

    Expected: workflow_step=explained_unfulfilled.
    """
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(email="unfulfilled@test.com", message="When will my order ship?"),
        )

    st = data["state"]
    assert st["is_escalated"] is False
    assert st["workflow_step"] == "explained_unfulfilled"

    # Tool trace confirms UNFULFILLED status
    traces = st["internal_data"]["tool_traces"]
    order_data = traces[0]["output"]["data"]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["order_id"] == "#2001"


# ── Test 3: DELIVERED order → told marked delivered ───────────────────


@pytest.mark.asyncio
async def test_wismo_delivered_order(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Email delivered@test.com → DELIVERED mock scenario.

    Expected: workflow_step=explained_delivered.
    """
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(email="delivered@test.com", message="Did my order arrive?"),
        )

    st = data["state"]
    assert st["is_escalated"] is False
    assert st["workflow_step"] == "explained_delivered"

    # Tool trace confirms DELIVERED status
    traces = st["internal_data"]["tool_traces"]
    order_data = traces[0]["output"]["data"]
    assert order_data["status"] == "DELIVERED"


# ── Test 4: No orders found → asks for order ID ──────────────────────


@pytest.mark.asyncio
async def test_wismo_no_orders_asks_for_id(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Email noorders@test.com → no orders mock.

    Expected: workflow_step=awaiting_order_id, assistant asks for order number.
    """
    from api.server import app

    conv_id = "wismo-noorders-%s" % uuid.uuid4().hex[:8]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(
                conv_id=conv_id,
                email="noorders@test.com",
                message="Hi, where is my BuzzPatch?",
            ),
        )

    st = data["state"]
    assert st["is_escalated"] is False
    assert st["workflow_step"] == "awaiting_order_id"
    assert st["last_assistant_message"] is not None
    # Should ask for order number
    assert "order" in st["last_assistant_message"].lower()


# ── Test 5: No orders → customer provides order ID → resolves ────────


@pytest.mark.asyncio
async def test_wismo_no_orders_then_provides_id(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Two-turn: first no orders (asks for ID), then customer gives #43189.

    Expected: second turn resolves with order details, workflow_step=wait_promise_set.
    """
    from api.server import app

    conv_id = "wismo-provide-id-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: no orders → asks for order ID
        turn1 = await _post_chat(
            client, {**base, "message": "Where is my order?"}
        )
        assert turn1["state"]["workflow_step"] == "awaiting_order_id"

        # Turn 2: customer provides order ID
        turn2 = await _post_chat(
            client, {**base, "message": "Oh sorry, it's order #43189"}
        )

    st2 = turn2["state"]
    assert st2["is_escalated"] is False
    assert st2["workflow_step"] == "wait_promise_set"  # resolved to IN_TRANSIT
    assert st2["last_assistant_message"] is not None

    # Tool traces should contain get_order_by_id with #43189
    traces = st2["internal_data"]["tool_traces"]
    by_id_traces = [t for t in traces if t["name"] == "get_order_by_id"]
    assert len(by_id_traces) >= 1
    assert by_id_traces[0]["output"]["data"]["order_id"] == "#43189"
    assert by_id_traces[0]["output"]["data"]["status"] == "IN_TRANSIT"


# ── Test 6: No orders → no ID given twice → escalates ────────────────


@pytest.mark.asyncio
async def test_wismo_no_orders_no_id_twice_escalates(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Three-turn: no orders, customer fails to provide ID twice → escalation.

    Turn 1: no orders → asks for ID
    Turn 2: customer says something without an order number → asks again
    Turn 3: still no order number → escalates to Monica
    """
    from api.server import app

    conv_id = "wismo-noid-esc-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: no orders
        t1 = await _post_chat(client, {**base, "message": "Where is my stuff?"})
        assert t1["state"]["workflow_step"] == "awaiting_order_id"

        # Turn 2: no order number in message
        t2 = await _post_chat(
            client, {**base, "message": "I don't know my order number"}
        )
        assert t2["state"]["workflow_step"] == "awaiting_order_id"
        assert t2["state"]["is_escalated"] is False

        # Turn 3: still no order number → escalates
        t3 = await _post_chat(
            client, {**base, "message": "I really can't find it"}
        )

    assert t3["state"]["is_escalated"] is True
    assert "Monica" in t3["state"]["last_assistant_message"]


# ── Test 7: Missing customer email → escalates immediately ───────────


@pytest.mark.asyncio
async def test_wismo_missing_email_escalates(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Empty customer email → immediate escalation.

    Expected: is_escalated=True, mentions looping in for support.
    """
    from api.server import app

    payload = _payload(email="", message="Where is my order?")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, payload)

    st = data["state"]
    assert st["is_escalated"] is True
    last_msg = st["last_assistant_message"]
    assert "Monica" in last_msg or "looping" in last_msg.lower()


# ── Test 8: Duplicate message detection ──────────────────────────────


@pytest.mark.asyncio
async def test_wismo_duplicate_message_blocked(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Sending the exact same message twice in same thread → duplicate detected."""
    from api.server import app

    conv_id = "wismo-dup-%s" % uuid.uuid4().hex[:8]
    payload = _payload(conv_id=conv_id, message="Order #43189 shows in transit for 10 days")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await _post_chat(client, payload)
        second = await _post_chat(client, payload)

    assert first["agent"] == "wismo"
    assert second["agent"] == "duplicate"


# ── Test 9: Multi-turn continuity (memory preserved) ──────────────────


@pytest.mark.asyncio
async def test_wismo_multiturn_memory(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Two different messages in same thread → both stored, thread grows."""
    from api.server import app

    conv_id = "wismo-mem-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(
            client, {**base, "message": "Order #43189 shows in transit for 10 days. Any update?"}
        )
        await _post_chat(
            client, {**base, "message": "Can you also share the tracking link?"}
        )

        thread = await _get_thread(client, conv_id)

    assert len(thread["messages"]) >= 4  # 2 user + 2 assistant
    user_msgs = [m["content"] for m in thread["messages"] if m["role"] == "user"]
    assert any("43189" in m for m in user_msgs)
    assert any("tracking" in m.lower() for m in user_msgs)


# ── Test 10: Escalation after missed promise date ─────────────────────


@pytest.mark.asyncio
async def test_wismo_missed_promise_escalates(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """If customer replies after the promised date and still IN_TRANSIT → escalate.

    Simulates: Turn 1 sets wait_promise, then we patch the saved state's
    wait_promise_until to a past date, then Turn 2 triggers escalation.
    """
    from api.server import app

    conv_id = "wismo-missed-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: normal → sets wait_promise
        t1 = await _post_chat(
            client, {**base, "message": "Where is my order?"}
        )
        assert t1["state"]["is_escalated"] is False
        assert t1["state"]["workflow_step"] == "wait_promise_set"

        # Manually patch the saved state so wait_promise_until is in the past
        saved_state = temp_db.load_state(conv_id)
        internal = saved_state.get("internal_data", {})
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        internal["wait_promise_until"] = yesterday
        saved_state["internal_data"] = internal
        temp_db.save_state(conv_id, saved_state)

        # Turn 2: customer replies after promised date → should escalate
        t2 = await _post_chat(
            client,
            {**base, "message": "It's past Friday and still not here!"},
        )

    assert t2["state"]["is_escalated"] is True
    last_msg = t2["state"]["last_assistant_message"]
    assert "Monica" in last_msg or "resend" in last_msg.lower()


# ── Test 11: Escalated thread blocks further auto-replies ─────────────


@pytest.mark.asyncio
async def test_wismo_escalated_thread_blocks_replies(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Once a thread is escalated, new messages should NOT generate agent replies.

    The server returns agent="escalated" with a different state structure
    containing status, reason, and escalation_summary.
    """
    from api.server import app

    # Use missing email to trigger immediate escalation
    conv_id = "wismo-block-%s" % uuid.uuid4().hex[:8]
    payload = _payload(conv_id=conv_id, email="", message="Hello?")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: escalates
        t1 = await _post_chat(client, payload)
        assert t1["state"]["is_escalated"] is True

        # Turn 2: should be blocked (already escalated)
        t2 = await _post_chat(
            client,
            {**payload, "customer_email": "", "message": "Are you there?"},
        )

    # The server returns agent="escalated" for already-escalated threads
    assert t2["agent"] == "escalated"
    assert t2["state"]["status"] == "escalated"
    assert t2["state"]["reason"] == "thread already escalated to human"


# ── Test 12: Wait-promise day logic ───────────────────────────────────


@pytest.mark.asyncio
async def test_wismo_wait_promise_day_logic(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """Verify the wait-promise day is correctly calculated based on today's day.

    The internal state should contain promise_day_label and wait_promise_until.
    We verify this by reading the saved full state from the checkpointer.
    """
    from api.server import app

    conv_id = "wismo-daylogic-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, {**base, "message": "Where is my order?"})

    assert data["state"]["workflow_step"] == "wait_promise_set"

    # Read the full state from DB to check wait promise details
    full_state = temp_db.load_state(conv_id)
    internal = full_state.get("internal_data", {})

    today = date.today()
    weekday = today.weekday()

    if 0 <= weekday <= 2:  # Mon-Wed
        assert internal.get("promise_day_label") == "Friday"
        expected_date = today + timedelta(days=(4 - weekday))
    else:  # Thu-Sun
        assert internal.get("promise_day_label") == "early next week"
        expected_date = today + timedelta(days=((7 - weekday) % 7 or 7))

    assert internal.get("wait_promise_until") == expected_date.isoformat()
    assert internal.get("decided_action") == "wait_promise"
    assert internal.get("order_status") == "IN_TRANSIT"


# ── Test 13: Tracking URL shared when in transit ──────────────────────


@pytest.mark.asyncio
async def test_wismo_tracking_url_in_tool_output(
    temp_db, mock_route_to_wismo, mock_wismo_llm
):
    """The get_order_status tool should return a tracking URL for IN_TRANSIT orders."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Can you confirm the estimated delivery date? Thanks!"),
        )

    traces = data["state"]["internal_data"]["tool_traces"]
    assert len(traces) >= 1

    # The mock returns tracking_url for IN_TRANSIT
    order_data = traces[0]["output"]["data"]
    assert order_data["tracking_url"] == "https://tracking.example.com/demo123"
    assert order_data["status"] == "IN_TRANSIT"
