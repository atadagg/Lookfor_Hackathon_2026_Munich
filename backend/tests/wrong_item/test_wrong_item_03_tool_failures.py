"""Wrong Item Test Suite 03: Tool Failures

Tool returns success=false or timeout → graceful handling / escalation.
See ROADMAP.md. (Stub: expand when agent is fully wired.)"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_wrong_item, post_chat


@pytest.fixture
def mock_route_to_wrong_item(monkeypatch):
    async def _route(state):
        state["intent"] = "Wrong / Missing Item in Parcel"
        state["routed_agent"] = "wrong_item"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_wrong_item_llm(monkeypatch):
    class FakeMessage:
        content = "I'm sorry. We're looking into it."
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
async def test_03_01_agent_handles_without_crash(temp_db, mock_route_to_wrong_item, mock_wrong_item_llm):
    """Agent runs without crash when tools are mocked (API_URL empty)."""
    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_wrong_item())
    assert data["agent"] == "wrong_item"
    assert data["state"]["is_escalated"] is False or data["state"]["last_assistant_message"]
