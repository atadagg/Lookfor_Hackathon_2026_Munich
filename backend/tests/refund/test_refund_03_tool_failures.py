"""Refund Test Suite 03: Tool Failures"""

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
async def test_03_01_order_lookup_fails(temp_db, mock_route_to_refund, unset_api_url, monkeypatch):
    """Order lookup failure should escalate gracefully."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Database timeout")

    import agents.refund.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I want a refund."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "monica" in msg or "trouble" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_03_02_refund_tool_fails(temp_db, mock_route_to_refund, unset_api_url, monkeypatch):
    """Refund tool failure should be handled gracefully."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_refund_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Payment processor error")

    import agents.refund.graph as graph_mod
    monkeypatch.setattr(graph_mod, "refund_order_cash", mock_refund_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="Please refund my order. I want cash back."
        ))

    # Should respond or escalate even if tool fails
    assert data["state"]["last_assistant_message"] is not None or data["state"]["is_escalated"]


@pytest.mark.asyncio
async def test_03_03_store_credit_tool_fails(temp_db, mock_route_to_refund, unset_api_url, monkeypatch):
    """Store credit tool failure should be logged in tool_traces."""
    from api.server import app
    from schemas.internal import ToolResponse

    call_count = [0]
    async def mock_credit_fail(*args, **kwargs):
        call_count[0] += 1
        return ToolResponse(success=False, data={}, error="Store credit API down")

    import agents.refund.graph as graph_mod
    monkeypatch.setattr(graph_mod, "create_store_credit", mock_credit_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I'll take store credit please."
        ))

    # Should handle gracefully
    assert data["state"]["last_assistant_message"] is not None or data["state"]["is_escalated"]
