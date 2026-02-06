"""Feedback Test Suite 02: Edge Cases"""

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
async def test_02_01_short_feedback(temp_db, mock_route_to_feedback, unset_api_url):
    """Very short feedback should still get warm response."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="Love it!"
        ))

    assert data["agent"] == "feedback"
    msg = data["state"].get("last_assistant_message") or ""
    assert any(emoji in msg for emoji in ["🥰", "🙏", "😊", "❤️"])


@pytest.mark.asyncio
async def test_02_02_very_enthusiastic_all_caps(temp_db, mock_route_to_feedback, unset_api_url):
    """All caps enthusiastic feedback."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="OMG!!! THESE PATCHES ARE ABSOLUTELY AMAZING!!! THANK YOU SO MUCH!!!"
        ))

    assert data["agent"] == "feedback"
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_02_03_feedback_with_recommendation(temp_db, mock_route_to_feedback, unset_api_url):
    """Feedback mentioning recommendations to friends."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="These patches are life-changing! I've already recommended them to 3 friends!"
        ))

    assert data["agent"] == "feedback"
    msg = (data["state"].get("last_assistant_message") or "")
    assert len(msg) > 20
