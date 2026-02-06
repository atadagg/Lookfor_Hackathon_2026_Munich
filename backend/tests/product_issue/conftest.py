"""Shared fixtures for product_issue tests."""

import os
import pathlib
import sys
import tempfile
import uuid

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        from core.database import Checkpointer
        cp = Checkpointer(db_path=path)
        monkeypatch.setattr("api.server.checkpointer", cp)
        yield cp
    finally:
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def mock_route_to_product_issue(monkeypatch):
    async def _route(state):
        state["intent"] = "Product Issue – No Effect"
        state["routed_agent"] = "product_issue"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_product_issue_llm(monkeypatch):
    """Mock LLM for product_issue agent (ConversationalAgent or graph generate_response node)."""
    class FakeMessage:
        content = (
            "I'm sorry to hear the patches aren't helping. Let me look into "
            "your order and understand what you're hoping to achieve."
        )
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


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    monkeypatch.setenv("API_URL", "")
