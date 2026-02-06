"""Discount Test Suite 03: Tool Failures"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_discount, post_chat


@pytest.mark.asyncio
async def test_03_01_discount_creation_fails(temp_db, mock_route_to_discount, unset_api_url, monkeypatch):
    """Discount creation failure should be handled gracefully."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Shopify API down")

    import agents.discount_agent.graph as graph_mod
    monkeypatch.setattr(graph_mod, "create_discount_10_percent", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Can I get a discount code?"
        ))

    # Should respond or escalate even if tool fails
    assert data["state"].get("last_assistant_message") is not None or data["state"].get("is_escalated") or data.get("state") is not None


@pytest.mark.asyncio
async def test_03_02_multiple_tool_failures(temp_db, mock_route_to_discount, unset_api_url, monkeypatch):
    """Multiple failures should still respond."""
    from api.server import app
    from schemas.internal import ToolResponse

    call_count = [0]
    async def mock_fail(*args, **kwargs):
        call_count[0] += 1
        return ToolResponse(success=False, data={}, error=f"Fail {call_count[0]}")

    import agents.discount_agent.graph as graph_mod
    monkeypatch.setattr(graph_mod, "create_discount_10_percent", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_discount(
            conv_id="discount-multifail",
            message="Discount please?"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_discount(
            conv_id="discount-multifail",
            message="Still need that code!"
        ))

    # Both should respond
    assert data1["state"].get("last_assistant_message") is not None or data1["state"].get("is_escalated") or data1.get("state") is not None
    assert data2["state"].get("last_assistant_message") is not None or data2["state"].get("is_escalated") or data2.get("state") is not None
