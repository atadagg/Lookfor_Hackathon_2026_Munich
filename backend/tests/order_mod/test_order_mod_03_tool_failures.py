"""Order Mod Test Suite 03: Tool Failures"""

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
async def test_03_01_order_lookup_fails(temp_db, mock_route_to_order_mod, unset_api_url, monkeypatch):
    """Order lookup failure should escalate gracefully."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="API timeout")

    import agents.order_mod.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="Cancel my order."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "trouble" in msg or "monica" in msg


@pytest.mark.asyncio
async def test_03_02_cancel_tool_fails(temp_db, mock_route_to_order_mod, unset_api_url, monkeypatch):
    """Cancel tool failure should be handled."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_cancel_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Shopify API error")

    import agents.order_mod.graph as graph_mod
    monkeypatch.setattr(graph_mod, "cancel_order", mock_cancel_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="Cancel my accidental order."
        ))

    # Should respond even if tool fails
    assert data["state"]["last_assistant_message"] is not None or data["state"]["is_escalated"]
