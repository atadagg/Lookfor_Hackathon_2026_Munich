"""Wrong Item Test Suite 04: Escalation Scenarios

Reship → must escalate. Store credit/refund → correct tags and confirmations.
See ROADMAP.md Step 5 and 6.
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
        content = "I'm sorry. I'm looping in Monica so we can get this sorted."
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
    # Patch where the client is used (conversational_agent imports it)
    monkeypatch.setattr("core.llm.get_async_openai_client", lambda: FakeClient(), raising=True)
    monkeypatch.setattr("core.conversational_agent.get_async_openai_client", lambda: FakeClient(), raising=True)


@pytest.mark.asyncio
async def test_04_01_escalation_message_mentions_support(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """When agent escalates, message should mention looping in support/Monica (ROADMAP 7.2)."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item())
    msg = (data["state"].get("last_assistant_message") or "").lower()
    # With mock: "looping in Monica". ROADMAP 7.2: escalation message should mention support/Monica.
    assert "monica" in msg or "loop" in msg or "support" in msg or "escalat" in msg or "take it from here" in msg
