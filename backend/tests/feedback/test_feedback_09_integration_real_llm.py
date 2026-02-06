"""Feedback Test Suite 09: Integration with Real LLM

IMPORTANT: This test uses real OpenAI API calls.
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_01_real_llm_enthusiastic_feedback(temp_db, mock_route_to_feedback, unset_api_url):
    """Real LLM: Enthusiastic feedback with emojis."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            first_name="Jessica",
            message="OMG! The BuzzPatch is AMAZING! My kids love them and no more mosquito bites!"
        ))

    assert data["agent"] == "feedback"
    msg = data["state"].get("last_assistant_message") or ""
    
    # Should have emojis
    has_emoji = any(emoji in msg for emoji in ["🥰", "🙏", "😊", "❤️", "🎉"])
    assert has_emoji, f"Should have emojis: {msg}"
    
    # Should mention review
    assert "review" in msg.lower() or "feedback" in msg.lower() or "trustpilot" in msg.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_02_real_llm_multiturn_review(temp_db, mock_route_to_feedback, unset_api_url):
    """Real LLM: Full review flow."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        data1 = await post_chat(client, payload_feedback(
            conv_id="feedback-real-1",
            first_name="Maria",
            message="The FocusPatch is incredible!"
        ))
        
        # Turn 2
        data2 = await post_chat(client, payload_feedback(
            conv_id="feedback-real-1",
            first_name="Maria",
            message="Yes! I'd love to leave a review!"
        ))

    # Second reply should have Trustpilot link
    msg2 = (data2["state"].get("last_assistant_message") or "").lower()
    assert "trustpilot" in msg2 or "review" in msg2
