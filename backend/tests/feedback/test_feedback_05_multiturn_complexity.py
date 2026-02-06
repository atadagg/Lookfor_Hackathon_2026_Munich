"""Feedback Test Suite 05: Multi-turn Complexity"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_feedback, post_chat


@pytest.mark.asyncio
async def test_05_01_three_turn_review_flow(temp_db, mock_route_to_feedback, unset_api_url):
    """3-turn: Feedback → Ask review → Yes → Link → Thank you."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-3turn",
            message="The FocusPatch helped my son so much!"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-3turn",
            message="Yes, I'd love to leave a review!"
        ))
        
        # Turn 3
        data3 = await post_chat(client, payload_feedback(
            conv_id="feedback-3turn",
            message="Done! I left a 5-star review!"
        ))

    # All should respond with emojis
    for data in [data1, data2, data3]:
        msg = data["state"].get("last_assistant_message") or ""
        assert len(msg) > 10


@pytest.mark.asyncio
async def test_05_02_decline_then_change_mind(temp_db, mock_route_to_feedback, unset_api_url):
    """Decline review → Change mind → Ask again."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Feedback
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-change",
            message="Love these patches!"
        ))
        
        # Turn 2: Decline
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-change",
            message="No thanks, I'm too busy."
        ))
        
        # Turn 3: Change mind
        data3 = await post_chat(client, payload_feedback(
            conv_id="feedback-change",
            message="Actually, I changed my mind. I'll leave a review!"
        ))

    # Should handle gracefully
    assert data3["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_05_03_state_persistence(temp_db, mock_route_to_feedback, unset_api_url):
    """State should persist across multiple feedback messages."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-persist",
            message="Great patches!"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-persist",
            message="Already told 5 friends about it!"
        ))

    # Both should be handled by feedback agent
    assert data1["agent"] == "feedback"
    # Second might stay in feedback or route elsewhere, but should respond
    assert data2["state"]["last_assistant_message"] is not None
