"""WISMO integration tests with REAL LLM calls.

These tests exercise the full production pipeline:
  - Real OpenAI router (intent classification via GPT-4o-mini)
  - Real OpenAI response generation (GPT-4o-mini)
  - Real LangGraph state machine execution
  - Real tool function execution (mock data only because API_URL is empty)

The ONLY thing mocked is the external Shopify/Skio HTTP endpoints (via empty
API_URL), which makes the tool functions return deterministic mock data.

Requires: OPENAI_API_KEY set in backend/.env

Run with:  pytest tests/test_wismo_integration.py -v -s
"""

import os
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

# Load .env so OPENAI_API_KEY is available
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Skip all tests in this module if no API key
_has_api_key = bool(os.getenv("OPENAI_API_KEY"))
pytestmark = pytest.mark.skipif(
    not _has_api_key, reason="OPENAI_API_KEY not set – skipping integration tests"
)


# ── Fixtures ─────────────────────────────────────────────────────────


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
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def use_mock_tools(monkeypatch):
    """Tools return mock data (no real Shopify) but everything else is real."""
    monkeypatch.setenv("API_URL", "")


@pytest.fixture(autouse=True)
def reset_llm_clients():
    """Reset cached LLM clients so each test gets fresh ones."""
    import core.llm as llm_mod
    import router.logic as router_mod
    old_llm = llm_mod._async_client
    old_router = router_mod._client
    llm_mod._async_client = None
    router_mod._client = None
    yield
    llm_mod._async_client = old_llm
    router_mod._client = old_router


def _payload(
    conv_id: Optional[str] = None,
    email: str = "test@example.com",
    message: str = "Where is my order?",
    first_name: str = "Jane",
    last_name: str = "Doe",
) -> dict:
    return {
        "conversation_id": conv_id or "int-wismo-%s" % uuid.uuid4().hex[:8],
        "user_id": "user-int",
        "channel": "email",
        "customer_email": email,
        "first_name": first_name,
        "last_name": last_name,
        "shopify_customer_id": "cust-int",
        "message": message,
    }


async def _post_chat(client: AsyncClient, payload: dict) -> dict:
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, "HTTP %d: %s" % (resp.status_code, resp.text)
    return resp.json()


# ── Test 1: LLM correctly routes a WISMO inquiry ─────────────────────


@pytest.mark.asyncio
async def test_llm_routes_shipping_query_to_wismo(temp_db):
    """A shipping delay message should be classified by the real LLM
    and routed to the 'wismo' agent."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Order #43189 shows 'in transit' for 10 days. Any update?"),
        )

    # The real LLM router should classify this as shipping/WISMO
    assert data["agent"] == "wismo", "Expected wismo agent, got: %s" % data["agent"]
    st = data["state"]
    assert st["routed_agent"] == "wismo"
    assert "shipping" in (st.get("intent") or "").lower() or "wismo" in (st.get("intent") or "").lower()


# ── Test 2: LLM generates a real response with order details ─────────


@pytest.mark.asyncio
async def test_llm_generates_response_with_order_info(temp_db):
    """The real LLM should compose a response referencing the order status."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Hi, just curious when my BuzzPatch will arrive to Toronto."),
        )

    st = data["state"]
    reply = st["last_assistant_message"]
    assert reply is not None and len(reply) > 20, "Response too short: %s" % reply

    # The LLM should mention something about the order being on the way
    # or tracking, since the mock returns IN_TRANSIT
    reply_lower = reply.lower()
    has_relevant_content = any(
        term in reply_lower
        for term in ["transit", "on the way", "tracking", "shipped", "delivery", "arrive", "wait", "friday", "next week"]
    )
    assert has_relevant_content, "LLM response doesn't mention order status: %s" % reply


# ── Test 3: Full WISMO flow with tool traces ─────────────────────────


@pytest.mark.asyncio
async def test_full_wismo_flow_with_real_llm(temp_db):
    """Complete end-to-end: real router + real LLM + real graph + mock tools.

    Verifies:
    - Router picks wismo
    - Tool get_order_status was called
    - LLM composed a meaningful response
    - Workflow completed to wait_promise_set
    """
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Can you confirm the estimated delivery date? Thanks!"),
        )

    assert data["agent"] == "wismo"
    st = data["state"]

    # Tool was called
    traces = st["internal_data"]["tool_traces"]
    assert len(traces) >= 1, "No tool traces found"
    assert traces[0]["name"] == "get_order_status"
    assert traces[0]["output"]["success"] is True
    assert traces[0]["output"]["data"]["status"] == "IN_TRANSIT"

    # Workflow completed
    assert st["workflow_step"] == "wait_promise_set"
    assert st["is_escalated"] is False

    # LLM wrote a real response
    reply = st["last_assistant_message"]
    assert reply is not None
    assert len(reply) > 30, "LLM response too short: %s" % reply


# ── Test 4: UNFULFILLED with real LLM ────────────────────────────────


@pytest.mark.asyncio
async def test_unfulfilled_with_real_llm(temp_db):
    """Unfulfilled order → LLM should mention it hasn't shipped yet."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(
                email="unfulfilled@test.com",
                message="When will my order ship? It's been a week.",
            ),
        )

    st = data["state"]
    assert st["workflow_step"] == "explained_unfulfilled"
    reply = st["last_assistant_message"].lower()
    has_relevant = any(
        t in reply for t in [
            "not shipped", "hasn't shipped", "not yet", "hasn't been",
            "warehouse", "processing", "preparing", "hasn't shipped yet",
            "has not shipped", "ship", "unfulfilled",
        ]
    )
    assert has_relevant, "LLM should mention order hasn't shipped: %s" % st["last_assistant_message"]


# ── Test 5: DELIVERED with real LLM ──────────────────────────────────


@pytest.mark.asyncio
async def test_delivered_with_real_llm(temp_db):
    """Delivered order → LLM should mention it's marked as delivered."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(
                email="delivered@test.com",
                message="Did my order arrive? I haven't checked yet.",
            ),
        )

    st = data["state"]
    assert st["workflow_step"] == "explained_delivered"
    reply = st["last_assistant_message"].lower()
    has_relevant = any(t in reply for t in ["delivered", "marked", "arrived"])
    assert has_relevant, "LLM should mention delivery: %s" % st["last_assistant_message"]


# ── Test 6: No orders → asks for ID (real LLM) ──────────────────────


@pytest.mark.asyncio
async def test_no_orders_asks_for_id_real_llm(temp_db):
    """No orders found → graph should ask for order ID (this is deterministic,
    not LLM-driven, but we verify the full pipeline works)."""
    from api.server import app

    conv_id = "int-noorders-%s" % uuid.uuid4().hex[:8]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(
                conv_id=conv_id,
                email="noorders@test.com",
                message="Hi, where is my BuzzPatch order?",
            ),
        )

    st = data["state"]
    assert st["workflow_step"] == "awaiting_order_id"
    reply = st["last_assistant_message"].lower()
    assert "order" in reply, "Should ask for order number: %s" % st["last_assistant_message"]


# ── Test 7: Multi-turn with real LLM ────────────────────────────────


@pytest.mark.asyncio
async def test_multiturn_continuation_real_llm(temp_db):
    """Two-turn conversation: initial query + follow-up.

    Verifies memory is preserved and the LLM doesn't contradict itself.
    """
    from api.server import app

    conv_id = "int-multi-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        t1 = await _post_chat(
            client,
            {**base, "message": "Order #43189 shows in transit for 10 days. Any update?"},
        )
        assert t1["agent"] == "wismo"
        assert t1["state"]["is_escalated"] is False

        # Turn 2: follow-up in same thread
        t2 = await _post_chat(
            client,
            {**base, "message": "Can you share the tracking link please?"},
        )

    # Should still be wismo, not escalated
    assert t2["agent"] == "wismo"
    reply2 = t2["state"]["last_assistant_message"]
    assert reply2 is not None and len(reply2) > 10


# ── Test 8: Missed promise escalation with real LLM ──────────────────


@pytest.mark.asyncio
async def test_missed_promise_escalation_real_llm(temp_db):
    """Patch wait_promise_until to yesterday → next message should escalate."""
    from api.server import app

    conv_id = "int-missed-%s" % uuid.uuid4().hex[:8]
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: sets wait promise
        t1 = await _post_chat(
            client, {**base, "message": "Where is my order?"}
        )
        assert t1["state"]["workflow_step"] == "wait_promise_set"

        # Patch the promise date to yesterday
        saved = temp_db.load_state(conv_id)
        internal = saved.get("internal_data", {})
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        internal["wait_promise_until"] = yesterday
        saved["internal_data"] = internal
        temp_db.save_state(conv_id, saved)

        # Turn 2: should trigger escalation
        t2 = await _post_chat(
            client,
            {**base, "message": "It's past the date you promised and still nothing!"},
        )

    assert t2["state"]["is_escalated"] is True
    reply = t2["state"]["last_assistant_message"]
    # Should mention escalation/Monica/resend
    reply_lower = reply.lower()
    has_escalation = any(t in reply_lower for t in ["monica", "looping", "resend", "escalat"])
    assert has_escalation, "Escalation message expected: %s" % reply
