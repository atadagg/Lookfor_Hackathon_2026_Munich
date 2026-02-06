"""Wrong Item Test Suite 05: Multi-Turn Complexity

Memory, duplicate detection, state across turns. See ROADMAP.md.
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_wrong_item, post_chat


@pytest.fixture
def mock_wrong_item_llm(monkeypatch):
    class FakeMessage:
        content = "I'm sorry. Can you tell me - wrong item or missing? A photo would help."
        tool_calls = None
    class FakeChoice:
        message = FakeMessage()
    class FakeCompletion:
        choices = [FakeChoice()]
    class FakeCompletions:
        async def create(self, *args, **kwargs):
            return FakeCompletion()
    class FakeChat:
        completions = FakeCompletions()
    class FakeClient:
        chat = FakeChat()
    monkeypatch.setattr("core.llm.get_async_openai_client", lambda: FakeClient(), raising=True)
    monkeypatch.setattr("core.conversational_agent.get_async_openai_client", lambda: FakeClient(), raising=True)


@pytest.mark.asyncio
async def test_05_01_multiturn_same_conversation(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Two messages in same conversation → both handled, no crash."""
    from api.server import app
    conv_id = f"wrong-multi-{uuid.uuid4().hex[:8]}"
    base = payload_wrong_item(conv_id=conv_id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        d1 = await post_chat(client, {**base, "message": "Got wrong stickers."})
        d2 = await post_chat(client, {**base, "message": "I want a replacement please."})
    assert d1["agent"] == "wrong_item"
    assert d2["agent"] == "wrong_item"
    assert d1["conversation_id"] == d2["conversation_id"]


@pytest.mark.asyncio
async def test_05_02_duplicate_message_detected(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Same message sent twice → duplicate detected."""
    from api.server import app
    conv_id = f"wrong-dup-{uuid.uuid4().hex[:8]}"
    payload = payload_wrong_item(conv_id=conv_id, message="Wrong item received.")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await post_chat(client, payload)
        second = await post_chat(client, payload)
    assert first["agent"] == "wrong_item"
    assert second["agent"] == "duplicate"
