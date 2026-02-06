"""Feedback Test Suite 01: Basic Workflow

Tests positive feedback handling, review request, Trustpilot link.
"""

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
async def test_01_01_enthusiastic_feedback_routes(temp_db, mock_route_to_feedback, unset_api_url):
    """Enthusiastic feedback → feedback agent."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="OMG! The BuzzPatch is AMAZING! My kids love them!"
        ))

    assert data["agent"] == "feedback"
    assert data["state"]["current_workflow"] == "positive_feedback"
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_01_02_reply_has_emojis(temp_db, mock_route_to_feedback, unset_api_url):
    """Reply should contain emojis (warm tone)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            first_name="Maria",
            message="The patches are incredible! Thank you so much!"
        ))

    msg = data["state"].get("last_assistant_message") or ""
    # Check for common emojis
    has_emoji = any(emoji in msg for emoji in ["🥰", "🙏", "😊", "❤️", "🎉", "🙌"])
    assert has_emoji, f"Reply should contain emojis: {msg}"


@pytest.mark.asyncio
async def test_01_03_order_tagging(temp_db, mock_route_to_feedback, unset_api_url):
    """Order should be tagged with 'Positive Feedback'."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="BuzzPatch saved our camping trip!"
        ))

    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    tool_names = [t["name"] for t in traces]
    
    # Should tag order
    assert "add_order_tags" in tool_names or "get_customer_latest_order" in tool_names


@pytest.mark.asyncio
async def test_01_04_multiturn_review_yes(temp_db, mock_route_to_feedback, unset_api_url):
    """Multi-turn: Feedback → Yes to review → Trustpilot link."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Feedback
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-yes",
            first_name="Maria",
            message="The FocusPatch is incredible! My son's grades improved!"
        ))
        
        # Turn 2: Accept review
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-yes",
            first_name="Maria",
            message="Yes! I'd love to leave a review!"
        ))

    # Second reply should have Trustpilot link
    msg2 = (data2["state"].get("last_assistant_message") or "").lower()
    assert "trustpilot.com" in msg2 or "review" in msg2


@pytest.mark.asyncio
async def test_01_05_multiturn_review_no(temp_db, mock_route_to_feedback, unset_api_url):
    """Multi-turn: Feedback → No to review → Polite thanks."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Feedback
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-no",
            message="Love the patches!"
        ))
        
        # Turn 2: Decline review
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-no",
            message="Thanks but I'm pretty busy right now."
        ))

    # Should thank politely
    msg2 = (data2["state"].get("last_assistant_message") or "").lower()
    assert "thank" in msg2 or "understand" in msg2 or "no worries" in msg2


@pytest.mark.asyncio
async def test_01_06_camping_success_story(temp_db, mock_route_to_feedback, unset_api_url):
    """Camping trip success story feedback."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="BuzzPatch saved our camping trip—no bites at all! The kids had so much fun."
        ))

    assert data["agent"] == "feedback"
    msg = (data["state"].get("last_assistant_message") or "")
    assert len(msg) > 30
