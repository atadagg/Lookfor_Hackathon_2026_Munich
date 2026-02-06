"""Discount Test Suite 09: Integration with Real LLM

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
from conftest import payload_discount, post_chat


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_01_real_llm_discount_request(temp_db, mock_route_to_discount, unset_api_url):
    """Real LLM: Discount code request."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            first_name="Alex",
            message="Hi! Do you have any discount codes I can use?"
        ))

    assert data["agent"] == "discount"
    msg = data["state"].get("last_assistant_message") or ""
    
    # Should mention code
    assert "NATPAT10" in msg.upper() or "discount" in msg.lower()
    
    # Should include instructions
    assert "checkout" in msg.lower() or "use" in msg.lower() or "apply" in msg.lower()
