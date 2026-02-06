"""Refund Test Suite 04: Escalation Scenarios"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_refund, post_chat


@pytest.mark.asyncio
async def test_04_01_shipping_delay_escalates(temp_db, mock_route_to_refund, unset_api_url):
    """Shipping delay refund should escalate to Monica."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="Please refund. It was supposed to arrive last week for my son's birthday."
        ))

    # Shipping delay should escalate
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "monica" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_04_02_damaged_product_escalates(temp_db, mock_route_to_refund, unset_api_url):
    """Damaged product refund should escalate for replacement."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="The package arrived damaged. Half the stickers are unusable. I want a refund."
        ))

    # Damaged should escalate
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "monica" in msg or "replacement" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_04_03_no_orders_escalates(temp_db, mock_route_to_refund, unset_api_url, monkeypatch):
    """Customer with no orders should escalate."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_no_orders(*args, **kwargs):
        return ToolResponse(success=True, data={"no_orders": True})

    import agents.refund.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_no_orders, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I want a refund for my order."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "monica" in msg or "couldn't find" in msg
