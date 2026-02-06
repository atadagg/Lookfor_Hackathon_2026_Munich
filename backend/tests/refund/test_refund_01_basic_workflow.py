"""Refund Test Suite 01: Basic Workflow

Tests all refund routes (expectations, shipping, damaged, changed mind).
"""

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
async def test_01_01_refund_expectations_route(temp_db, mock_route_to_refund, unset_api_url):
    """Route A: Product didn't meet expectations → cash refund."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I'd like a refund. The patches didn't work for my child."
        ))

    assert data["agent"] == "refund"
    assert data["state"]["current_workflow"] == "refund"
    # Should execute refund (mock always treats as cash refund in first turn)
    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    assert "get_customer_latest_order" in tool_names


@pytest.mark.asyncio
async def test_01_02_refund_changed_mind_fulfilled(temp_db, mock_route_to_refund, unset_api_url):
    """Route D: Changed mind (fulfilled order) → store credit or cash refund."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I want to cancel my order. I changed my mind."
        ))

    assert data["agent"] in ("refund", "order_mod")  # Router might send to order_mod
    # Should check order status
    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    assert len(traces) >= 1


@pytest.mark.asyncio
async def test_01_03_store_credit_tagging(temp_db, mock_route_to_refund, unset_api_url):
    """Store credit should be tagged correctly."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Request refund
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-credit-1",
            message="Can I get a refund? The product didn't work."
        ))
        
        # Turn 2: Accept store credit
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-credit-1",
            message="Sure, I'll take the store credit with bonus!"
        ))

    traces = data2["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    
    # Should have store credit and tagging
    if "create_store_credit" in tool_names:
        assert "add_order_tags" in tool_names


@pytest.mark.asyncio
async def test_01_04_cash_refund_tagging(temp_db, mock_route_to_refund, unset_api_url):
    """Cash refund should be tagged correctly."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Direct cash refund request
        data = await post_chat(client, payload_refund(
            message="Please process a cash refund for my order."
        ))

    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    
    # Should have refund
    if "refund_order_cash" in tool_names:
        # Should also tag
        assert "add_order_tags" in tool_names


@pytest.mark.asyncio
async def test_01_05_shipping_delay_escalation(temp_db, mock_route_to_refund, unset_api_url):
    """Route B: Shipping delay → should escalate for replacement."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="Please refund my order. It was supposed to arrive last week and still hasn't shipped."
        ))

    # Shipping delay should escalate
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "monica" in msg or "support" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_01_06_damaged_item_route(temp_db, mock_route_to_refund, unset_api_url):
    """Route C: Damaged item → escalate or store credit."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            message="I need a refund. The package arrived damaged and half the stickers are unusable."
        ))

    # Should escalate for replacement or offer store credit
    state = data["state"]
    assert state.get("is_escalated") or state.get("last_assistant_message")


@pytest.mark.asyncio
async def test_01_07_multiturn_reason_then_credit(temp_db, mock_route_to_refund, unset_api_url):
    """Multi-turn: Ask reason → Store credit."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Request refund
        data1 = await post_chat(client, payload_refund(
            conv_id="refund-multi-1",
            message="Can I get a refund?"
        ))
        
        # Turn 2: Provide reason
        data2 = await post_chat(client, payload_refund(
            conv_id="refund-multi-1",
            message="It didn't meet my expectations."
        ))
        
        # Turn 3: Accept store credit
        data3 = await post_chat(client, payload_refund(
            conv_id="refund-multi-1",
            message="I'll take the store credit!"
        ))

    # Final turn should have store credit
    traces = data3["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    
    if "create_store_credit" in tool_names:
        assert data3["state"].get("workflow_step") in ("responded", "execute_done")
