"""Subscription Test Suite 09: Integration with Real LLM"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_subscription, post_chat


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_01_real_llm_cancel_request(temp_db, mock_route_to_subscription, unset_api_url):
    """Real LLM: Subscription cancel request."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            first_name="Sarah",
            message="I want to cancel my subscription. I have too many patches."
        ))

    assert data["agent"] == "subscription"
    assert data.get("state") is not None
    msg = data["state"].get("last_assistant_message") or ""
    assert len(msg) > 20
