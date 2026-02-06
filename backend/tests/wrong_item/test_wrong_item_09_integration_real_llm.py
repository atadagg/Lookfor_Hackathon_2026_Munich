"""Wrong Item Test Suite 09: Integration with Real LLM

Requires OPENAI_API_KEY. Verifies routing and real responses.
"""

import os
import pathlib
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import temp_db, payload_wrong_item, post_chat

_has_api_key = bool(os.getenv("OPENAI_API_KEY"))
pytestmark = pytest.mark.skipif(not _has_api_key, reason="OPENAI_API_KEY not set")


@pytest.fixture
def mock_route_to_wrong_item(monkeypatch):
    async def _route(state):
        state["intent"] = "Wrong / Missing Item in Parcel"
        state["routed_agent"] = "wrong_item"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.mark.asyncio
async def test_09_01_real_llm_responds_to_wrong_item(temp_db, mock_route_to_wrong_item):
    """Real LLM should produce an apologetic reply and ask what happened or for photo."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item(message="Got Zen stickers instead of Focus—help!"))
    assert data["agent"] == "wrong_item"
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert len(msg) > 30
    has_relevant = "sorry" in msg or "photo" in msg or "missing" in msg or "wrong" in msg or "apolog" in msg
    assert has_relevant, f"Reply should be apologetic or ask what happened: {msg}"
