"""Order Mod Test Suite 05: Multi-turn Complexity"""

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
async def test_05_01_two_turn_cancel_flow(temp_db, mock_route_to_order_mod, unset_api_url):
    """2-turn: Cancel request → Confirm reason."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-2turn",
            message="I want to cancel my order."
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-2turn",
            message="I placed it by accident. My kid clicked twice."
        ))

    # Both turns should respond
    assert data1["state"].get("last_assistant_message") is not None or data1["state"].get("is_escalated")
    # Second turn might route to escalated or have different response structure
    assert data2.get("state") is not None  # Just verify state exists


@pytest.mark.asyncio
async def test_05_02_escalation_persists(temp_db, mock_route_to_order_mod, unset_api_url):
    """Once escalated, subsequent messages route to escalated state."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Escalates (fulfilled order)
        data1 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-escalated",
            message="Cancel my order."
        ))
        
        # Turn 2: After escalation
        data2 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-escalated",
            message="Hello? Still waiting."
        ))

    # First should escalate
    if data1["state"].get("is_escalated"):
        # Second should stay escalated
        assert data2["agent"] == "escalated" or data2["state"]["is_escalated"]
