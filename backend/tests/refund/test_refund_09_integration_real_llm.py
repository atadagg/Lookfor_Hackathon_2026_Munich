"""Refund Test Suite 09: Integration with Real LLM

IMPORTANT: This test uses real OpenAI API calls.
Set OPENAI_API_KEY in .env before running.
"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_refund, post_chat


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_01_real_llm_refund_flow(temp_db, mock_route_to_refund, unset_api_url):
    """Real LLM: Full refund conversation with expectations route."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            conv_id="refund-real-llm-1",
            first_name="Sarah",
            message="I'd like a refund. The SleepyPatch didn't work for my daughter."
        ))

    # Should route to refund and respond
    assert data["agent"] == "refund"
    assert data["state"]["last_assistant_message"] is not None
    
    # Should call order lookup
    traces = data["state"].get("internal_data", {}).get("tool_traces", [])
    assert len(traces) >= 1
    
    # Reply should be empathetic
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert len(msg) > 30


@pytest.mark.integration
@pytest.mark.asyncio
async def test_09_02_real_llm_changed_mind(temp_db, mock_route_to_refund, unset_api_url):
    """Real LLM: Changed mind refund."""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            first_name="Kate",
            message="I changed my mind about my order. Can I get a refund?"
        ))

    assert data["agent"] in ("refund", "order_mod")
    assert data["state"]["last_assistant_message"] is not None
