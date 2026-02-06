"""Refund Test Suite 05: Multi-turn Complexity"""

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
async def test_05_01_three_turn_conversation(temp_db, mock_route_to_refund, unset_api_url):
    """3-turn: Request → Reason → Accept credit."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-3turn",
            message="Can I get a refund?"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-3turn",
            message="The product didn't meet my expectations."
        ))
        
        # Turn 3
        data3 = await post_chat(client, payload_refund(
            conv_id="refund-3turn",
            message="I'll take the store credit with bonus!"
        ))

    # Should maintain state across turns
    assert data1["state"]["workflow_step"] is not None
    assert data2["state"]["workflow_step"] is not None
    assert data3["state"]["workflow_step"] is not None


@pytest.mark.asyncio
async def test_05_02_change_mind_mid_conversation(temp_db, mock_route_to_refund, unset_api_url):
    """Customer changes mind during conversation (credit → cash)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Ask for refund
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-change",
            message="I want a refund please."
        ))
        
        # Turn 2: Decline store credit
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-change",
            message="No thanks to store credit. I want cash refund."
        ))

    # Should handle changed preference
    assert data2["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_05_03_escalation_persists(temp_db, mock_route_to_refund, unset_api_url, monkeypatch):
    """Once escalated, subsequent messages shouldn't re-process."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_no_orders(*args, **kwargs):
        return ToolResponse(success=True, data={"no_orders": True})

    import agents.refund.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_no_orders, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Escalates (no orders)
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-escalated",
            message="I want a refund."
        ))
        
        # Turn 2: After escalation
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-escalated",
            message="Hello? Anyone there?"
        ))

    assert data1["state"]["is_escalated"] is True
    # Second message goes to escalated state
    assert data2["agent"] == "escalated" or data2["state"]["is_escalated"]


@pytest.mark.asyncio
async def test_05_04_four_turn_expectations_flow(temp_db, mock_route_to_refund, unset_api_url):
    """4-turn: Request → Reason → Offer swap → Decline → Credit."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-4turn",
            message="I'd like a refund."
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-4turn",
            message="The patches didn't meet my expectations."
        ))
        
        # Turn 3
        data3 = await post_chat(client, payload_refund(
            conv_id="refund-4turn",
            message="No thanks to a swap. Just refund please."
        ))
        
        # Turn 4
        data4 = await post_chat(client, payload_refund(
            conv_id="refund-4turn",
            message="OK, I'll take store credit."
        ))

    # All turns should respond
    for data in [data1, data2, data3, data4]:
        assert data["state"]["last_assistant_message"] is not None or data["state"]["is_escalated"]
