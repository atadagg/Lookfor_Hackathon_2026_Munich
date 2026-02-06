"""Feedback Test Suite 04: Escalation Scenarios"""

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
async def test_04_01_feedback_should_not_escalate(temp_db, mock_route_to_feedback, unset_api_url):
    """Positive feedback should never escalate (unless unrelated issue)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="The patches are great! Thank you!"
        ))

    # Should not escalate
    assert data["state"]["is_escalated"] is False


@pytest.mark.asyncio
async def test_04_02_mixed_feedback_and_question(temp_db, mock_route_to_feedback, unset_api_url):
    """Feedback + unrelated question should still respond warmly."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="Love the patches! By the way, when will my next order ship?"
        ))

    # Should respond (might be routed to different agent on follow-up)
    assert data["state"]["last_assistant_message"] is not None
