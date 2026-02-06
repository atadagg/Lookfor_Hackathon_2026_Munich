"""Product Issue Test Suite 03: Tool Failures

Tests that the graph escalates deterministically when Shopify tools fail.

Graph nodes call tools directly (not via LLM function-calling), so
tool failures must be caught and handled:
- shopify_get_customer_orders fails → escalate
- shopify_get_order_details fails → escalate
- shopify_create_store_credit fails → escalate
- shopify_refund_order fails → escalate
- shopify_add_tags fails → still complete (tagging is best-effort)

ALL tests MUST FAIL against the current ConversationalAgent (which
doesn't call tools deterministically from graph nodes).
"""

import pathlib
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _payload(conv_id=None, email="test@example.com", message="Focus patches aren't helping.", **kwargs):
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


# ── Test 03.01: shopify_get_customer_orders fails → escalates ────────────────


@pytest.mark.asyncio
async def test_03_01_order_lookup_failure_escalates(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """When shopify_get_customer_orders returns success=false, graph must escalate."""
    import tools.shopify as shopify_mod

    async def _failing_get_customer_orders(**kwargs):
        return {"success": False, "data": {}, "error": "Shopify API 500"}

    monkeypatch.setattr(shopify_mod, "shopify_get_customer_orders", _failing_get_customer_orders)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["is_escalated"] is True
    assert data["state"]["workflow_step"].startswith("escalated")
    msg = (data["state"]["last_assistant_message"] or "").lower()
    assert "monica" in msg or "looping" in msg


# ── Test 03.02: shopify_get_order_details fails → escalates ─────────────────


@pytest.mark.asyncio
async def test_03_02_order_details_failure_escalates(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """When shopify_get_order_details returns success=false, graph must escalate."""
    import tools.shopify as shopify_mod

    async def _failing_get_order_details(**kwargs):
        return {"success": False, "data": {}, "error": "Order not found"}

    monkeypatch.setattr(shopify_mod, "shopify_get_order_details", _failing_get_order_details)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["is_escalated"] is True
    assert data["state"]["workflow_step"].startswith("escalated")


# ── Test 03.03: Tool error message preserved in escalation ───────────────────


@pytest.mark.asyncio
async def test_03_03_tool_error_preserved(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """Tool error details must appear in the escalation_summary."""
    import tools.shopify as shopify_mod

    async def _failing(**kwargs):
        return {"success": False, "data": {}, "error": "Shopify rate limit exceeded"}

    monkeypatch.setattr(shopify_mod, "shopify_get_customer_orders", _failing)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["is_escalated"] is True
    summary = data["state"].get("escalation_summary") or {}
    assert summary, "escalation_summary must be populated on tool failure"
    summary_str = str(summary).lower()
    assert "rate limit" in summary_str or "error" in summary_str


# ── Test 03.04: Tool raises exception → escalates ───────────────────────────


@pytest.mark.asyncio
async def test_03_04_tool_exception_escalates(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """If a tool raises an unhandled exception, graph must catch and escalate."""
    import tools.shopify as shopify_mod

    async def _exploding(**kwargs):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(shopify_mod, "shopify_get_customer_orders", _exploding)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    # Must not 500; must escalate gracefully
    assert data["state"]["is_escalated"] is True


# ── Test 03.05: Tool traces recorded even on failure ────────────────────────


@pytest.mark.asyncio
async def test_03_05_tool_traces_on_failure(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """Even when a tool fails, the call must appear in tool_traces for observability."""
    import tools.shopify as shopify_mod

    async def _failing(**kwargs):
        return {"success": False, "data": {}, "error": "Timeout"}

    monkeypatch.setattr(shopify_mod, "shopify_get_customer_orders", _failing)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    traces = data["state"]["internal_data"]["tool_traces"]
    order_calls = [t for t in traces if t["name"] == "shopify_get_customer_orders"]
    assert len(order_calls) >= 1, "Failed tool call must still be in tool_traces"
    assert order_calls[0]["output"]["success"] is False


# ── Test 03.06: Escalation message is customer-friendly ──────────────────────


@pytest.mark.asyncio
async def test_03_06_escalation_message_customer_friendly(temp_db, mock_route_to_product_issue, mock_product_issue_llm, monkeypatch):
    """Escalation message must not leak internal error details to the customer."""
    import tools.shopify as shopify_mod

    async def _failing(**kwargs):
        return {"success": False, "data": {}, "error": "SQL injection detected in parameter"}

    monkeypatch.setattr(shopify_mod, "shopify_get_customer_orders", _failing)

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    msg = (data["state"]["last_assistant_message"] or "").lower()
    assert "sql" not in msg, "Internal error details must not leak to customer"
    assert "injection" not in msg
    # Should mention handoff to human
    assert "monica" in msg or "looping" in msg or "support" in msg
