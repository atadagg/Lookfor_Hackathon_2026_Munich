"""Order Mod Test Suite 04: Escalation Scenarios"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_order_mod, post_chat


@pytest.mark.asyncio
async def test_04_01_fulfilled_order_escalates(temp_db, mock_route_to_order_mod, unset_api_url):
    """Fulfilled order modification should escalate."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock returns FULFILLED by default
        data = await post_chat(client, payload_order_mod(
            message="Cancel my order please."
        ))

    # Should escalate (fulfilled can't be modified)
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "fulfilled" in msg or "monica" in msg or "can't" in msg


@pytest.mark.asyncio
async def test_04_02_no_orders_escalates(temp_db, mock_route_to_order_mod, unset_api_url, monkeypatch):
    """No orders found should escalate."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_no_orders(*args, **kwargs):
        return ToolResponse(success=True, data={"no_orders": True})

    import agents.order_mod.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_no_orders, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="Update my shipping address."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "couldn't find" in msg or "monica" in msg
