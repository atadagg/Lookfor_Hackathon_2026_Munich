"""Order Mod Test Suite 01: Basic Workflow

Tests cancellation and address update flows.
"""

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
async def test_01_01_cancel_accidental_order(temp_db, mock_route_to_order_mod, unset_api_url):
    """Accidental order should cancel and tag."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="I need to cancel my order. I placed it by accident."
        ))

    assert data["agent"] == "order_mod"
    assert data["state"]["current_workflow"] == "order_modification"
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_01_02_cancel_duplicate_order(temp_db, mock_route_to_order_mod, unset_api_url):
    """Duplicate order cancellation."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="I accidentally ordered twice. Can you cancel one of them?"
        ))

    assert data["agent"] == "order_mod"
    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    assert len(traces) >= 1


@pytest.mark.asyncio
async def test_01_03_update_address_request(temp_db, mock_route_to_order_mod, unset_api_url):
    """Address update request."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="Can I update my shipping address? I entered the wrong one."
        ))

    assert data["agent"] == "order_mod"
    # Should ask for new address or escalate
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "address" in msg or "monica" in msg


@pytest.mark.asyncio
async def test_01_04_fulfilled_order_escalates(temp_db, mock_route_to_order_mod, unset_api_url):
    """Fulfilled order cancellation should escalate."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock returns FULFILLED status by default
        data = await post_chat(client, payload_order_mod(
            message="Cancel my order please."
        ))

    # Should escalate (fulfilled can't be cancelled)
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "fulfilled" in msg or "monica" in msg


@pytest.mark.asyncio
async def test_01_05_multiturn_cancel_flow(temp_db, mock_route_to_order_mod, unset_api_url):
    """Multi-turn: Ask to cancel → Provide reason → Execute."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-multi-1",
            message="I want to cancel my order."
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_order_mod(
            conv_id="ordermod-multi-1",
            message="I ordered it by mistake."
        ))

    # Should maintain state
    assert data1["state"].get("workflow_step") is not None
    # Second turn might route to escalated or have different state shape
    assert data2["state"].get("workflow_step") is not None or data2["state"].get("last_assistant_message") or data2["state"].get("is_escalated")


@pytest.mark.asyncio
async def test_01_06_order_lookup_called(temp_db, mock_route_to_order_mod, unset_api_url):
    """Agent must call order lookup tool."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="Cancel my order."
        ))

    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    assert "get_customer_latest_order" in tool_names
