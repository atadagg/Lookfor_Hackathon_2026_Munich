"""Order Mod Test Suite 09: Integration with Real LLM

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
from conftest import payload_order_mod, post_chat


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_01_real_llm_cancel_accidental(temp_db, mock_route_to_order_mod, unset_api_url):
    """Real LLM: Accidental order cancellation."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            first_name="Chris",
            message="I need to cancel my order. I placed it by accident."
        ))

    assert data["agent"] == "order_mod"
    assert data["state"]["last_assistant_message"] is not None
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert len(msg) > 20
