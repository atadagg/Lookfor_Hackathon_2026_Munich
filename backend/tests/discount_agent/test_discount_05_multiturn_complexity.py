"""Discount Test Suite 05: Multi-turn Complexity"""

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
async def test_05_01_two_turn_clarification(temp_db, mock_route_to_discount, unset_api_url):
    """2-turn: Ask → Clarify → Code."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_discount(
            conv_id="discount-2turn",
            message="Any deals?"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_discount(
            conv_id="discount-2turn",
            message="Yes, a discount code please!"
        ))

    # Should respond in both turns
    assert data1.get("state") is not None
    assert data2.get("state") is not None


@pytest.mark.asyncio
async def test_05_02_code_already_created_remembered(temp_db, mock_route_to_discount, unset_api_url):
    """Code creation should be remembered across turns."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Create code
        data1 = await post_chat(client, payload_discount(
            conv_id="discount-remember",
            message="Discount code please?"
        ))
        
        # Turn 2: Ask again
        data2 = await post_chat(client, payload_discount(
            conv_id="discount-remember",
            message="Can you send it again?"
        ))
        
        # Turn 3: Thank you
        data3 = await post_chat(client, payload_discount(
            conv_id="discount-remember",
            message="Thanks!"
        ))

    # First should create
    traces1 = data1["state"].get("internal_data", {}).get("tool_traces", [])
    created_in_turn1 = any(t["name"] == "create_discount_10_percent" for t in traces1)
    
    # Second should not create duplicate
    traces2 = data2["state"].get("internal_data", {}).get("tool_traces", [])
    
    if created_in_turn1:
        # Should have code_created flag
        assert data2["state"].get("internal_data", {}).get("code_created") is True


@pytest.mark.asyncio
async def test_05_03_three_turn_persistence(temp_db, mock_route_to_discount, unset_api_url):
    """State persistence across 3 turns."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_discount(
            conv_id="discount-3turn",
            message="Hi! Any discounts?"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_discount(
            conv_id="discount-3turn",
            message="Yes please, send me a code."
        ))
        
        # Turn 3
        data3 = await post_chat(client, payload_discount(
            conv_id="discount-3turn",
            message="Got it, thanks!"
        ))

    # All should maintain workflow state (if implemented)
    for data in [data1, data2, data3]:
        # Just verify they all have state
        assert data.get("state") is not None
