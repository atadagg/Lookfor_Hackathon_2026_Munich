"""Wrong Item Test Suite 02: Edge Cases

Missing data, malformed input, unicode, etc. See ROADMAP.md.
"""

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
        content = "I'm sorry to hear that. Can you tell me what happened?"
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
async def test_02_01_missing_email_handled(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Missing customer_email should not crash."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item(email=""))
    assert data["agent"] in ("wrong_item", "escalated")


@pytest.mark.asyncio
async def test_02_02_empty_message_handled(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Empty message should not crash."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item(message=""))
    assert data["agent"] in ("wrong_item", "escalated")


@pytest.mark.asyncio
async def test_02_03_unicode_handled(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Unicode in message should not break processing."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item(message="Wrong item 😤 Ça va?"))
    assert data["agent"] == "wrong_item"
