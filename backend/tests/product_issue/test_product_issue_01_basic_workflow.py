"""Product Issue Test Suite 01: Basic Workflow - Happy Paths

Tests the deterministic graph nodes of the Product Issue – No Effect workflow.

Expected graph structure:
    check_order ──> ask_goal ──> END  (workflow_step = "awaiting_goal")

On first message the graph MUST:
1. Look up the customer's order via shopify_get_customer_orders.
2. Fetch order details via shopify_get_order_details.
3. Store order_id, order_gid, product info in internal_data.
4. Set workflow_step = "awaiting_goal".
5. Generate an empathetic response asking the customer's goal.

ALL of these tests MUST FAIL against the current ConversationalAgent
implementation (which doesn't set workflow_step, doesn't call tools
deterministically, etc.).  They will pass only once the LangGraph-based
workflow is implemented.
"""

import pathlib
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _payload(conv_id=None, email="test@example.com", message="Focus patches aren't helping my son concentrate.", **kwargs):
    return {
        "conversation_id": conv_id or f"pi-{uuid.uuid4().hex[:8]}",
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


# ── Test 01.01: First message sets workflow_step to awaiting_goal ────────────


@pytest.mark.asyncio
async def test_01_01_first_message_sets_awaiting_goal(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """First complaint → check order → ask goal.  workflow_step must be 'awaiting_goal'."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"
    assert data["state"]["is_escalated"] is False


# ── Test 01.02: Order lookup recorded in tool_traces ─────────────────────────


@pytest.mark.asyncio
async def test_01_02_order_lookup_in_tool_traces(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Graph must call order lookup (get_order_and_product or shopify_get_customer_orders); trace recorded."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    traces = data["state"]["internal_data"]["tool_traces"]
    order_lookups = [
        t for t in traces
        if t["name"] in ("get_order_and_product", "shopify_get_customer_orders")
    ]
    assert len(order_lookups) >= 1, "Expected order lookup in tool_traces"


# ── Test 01.03: Order data stored in internal_data ───────────────────────────


@pytest.mark.asyncio
async def test_01_03_order_data_stored(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """After check_order node, order_id and order_gid must be in internal_data."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    internal = data["state"]["internal_data"]
    assert internal.get("order_id") is not None, "order_id must be set after check_order"
    assert internal.get("order_gid") is not None, "order_gid must be set after check_order"


# ── Test 01.04: Mosquito example → awaiting_goal ────────────────────────────


@pytest.mark.asyncio
async def test_01_04_mosquito_complaint_awaiting_goal(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """'Kids still getting bitten' → check order → awaiting_goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Kids still getting bitten even with 2 stickers on."),
        )

    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 01.05: Itch relief example → awaiting_goal ─────────────────────────


@pytest.mark.asyncio
async def test_01_05_itch_relief_complaint_awaiting_goal(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """'Itch relief patch did nothing' → check order → awaiting_goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Itch relief patch did nothing for the sting."),
        )

    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 01.06: Focus example → awaiting_goal ───────────────────────────────


@pytest.mark.asyncio
async def test_01_06_focus_complaint_awaiting_goal(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """'Focus patches aren't helping' → check order → awaiting_goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Focus patches aren't helping my son concentrate."),
        )

    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 01.07: Response contains empathy and asks about goal ────────────────


@pytest.mark.asyncio
async def test_01_07_response_empathy_and_goal_question(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Response must be empathetic AND ask about the customer's goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Sleep patches aren't helping my daughter."),
        )

    msg = (data["state"]["last_assistant_message"] or "").lower()
    # Must contain a question mark (asking about goal/usage)
    assert "?" in msg, "Response must ask the customer about their goal"
    # Must show empathy
    empathy_words = ("sorry", "hear", "understand", "tough", "frustrat")
    assert any(w in msg for w in empathy_words), "Response must show empathy"


# ── Test 01.08: current_workflow set to product_issue ────────────────────────


@pytest.mark.asyncio
async def test_01_08_current_workflow_set(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """current_workflow must be 'product_issue'."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["current_workflow"] == "product_issue"
