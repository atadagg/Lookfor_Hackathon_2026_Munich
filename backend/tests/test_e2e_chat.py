"""End-to-end tests for the /chat API.

Exercises the full flow: Request → Server → Router → Agent → Response.

Uses mocks for external services (router LLM, WISMO response LLM) so tests
run without API keys and are deterministic. Tools use the mock path when
API_URL is unset.

Run with: pytest tests/test_e2e_chat.py -v
"""

import pathlib
import sys
import tempfile
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Must patch before importing app (app captures checkpointer at import).
@pytest.fixture
def temp_db(monkeypatch):
    """Use an isolated temp SQLite DB for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        from core.database import Checkpointer

        cp = Checkpointer(db_path=path)
        monkeypatch.setattr("api.server.checkpointer", cp)
        yield path
    finally:
        import os

        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def mock_route_to_wismo(monkeypatch):
    """Bypass real LLM and always route to WISMO."""

    async def _route(state):
        state["intent"] = "Shipping Delay – Neutral Status Check"
        state["routed_agent"] = "wismo"
        return state

    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_wismo_llm(monkeypatch):
    """Bypass real LLM in WISMO generate_response node."""

    class FakeMessage:
        content = "Hi! Your order #1001 is on the way. You can track it here: https://tracking.example.com/demo123"

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
    """Ensure tools use mock path (no real API calls)."""
    monkeypatch.setenv("API_URL", "")


@pytest.mark.asyncio
async def test_chat_e2e_wismo_full_flow(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """POST /chat → routes to WISMO → runs graph → returns assistant reply."""

    from api.server import app

    payload = {
        "conversation_id": f"e2e-{uuid.uuid4().hex[:12]}",
        "user_id": "user-123",
        "channel": "email",
        "customer_email": "test@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "shopify_customer_id": "cust-456",
        "message": "Where is my order?",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/chat", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] == payload["conversation_id"]
    assert data["agent"] == "wismo"
    assert data["state"]["routed_agent"] == "wismo"
    assert data["state"]["current_workflow"] == "shipping"
    assert data["state"]["is_escalated"] is False
    assert data["state"]["last_assistant_message"] is not None
    assert "order" in data["state"]["last_assistant_message"].lower()
    assert "tracking" in data["state"]["last_assistant_message"].lower()


@pytest.mark.asyncio
async def test_chat_e2e_thread_endpoint(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """After a chat, GET /thread/{id} returns the thread with messages."""

    from api.server import app

    conv_id = f"e2e-thread-{uuid.uuid4().hex[:12]}"
    payload = {
        "conversation_id": conv_id,
        "user_id": "user-1",
        "customer_email": "jane@test.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "shopify_customer_id": "c1",
        "message": "Where is my order?",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        chat_resp = await client.post("/chat", json=payload)
        assert chat_resp.status_code == 200

        thread_resp = await client.get(f"/thread/{conv_id}")

    assert thread_resp.status_code == 200
    thread = thread_resp.json()
    assert thread["conversation_id"] == conv_id
    assert thread["status"] == "open"
    assert thread["current_workflow"] == "shipping"
    assert len(thread["messages"]) >= 2  # user + assistant
    roles = [m["role"] for m in thread["messages"]]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_chat_e2e_duplicate_message_skipped(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """Identical back-to-back messages are treated as duplicates."""

    from api.server import app

    conv_id = f"e2e-dup-{uuid.uuid4().hex[:12]}"
    payload = {
        "conversation_id": conv_id,
        "user_id": "user-1",
        "customer_email": "test@test.com",
        "first_name": "A",
        "last_name": "B",
        "shopify_customer_id": "c1",
        "message": "Where is my order?",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/chat", json=payload)
        second = await client.post("/chat", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["agent"] == "wismo"
    assert second.json()["agent"] == "duplicate"
    assert "Duplicate" in second.json()["state"]["warning"]


@pytest.mark.asyncio
async def test_chat_e2e_continuation_existing_conversation(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """New email in an existing conversation loads prior state and appends message."""

    from api.server import app

    conv_id = f"e2e-cont-{uuid.uuid4().hex[:12]}"
    base_payload = {
        "conversation_id": conv_id,
        "user_id": "user-1",
        "customer_email": "test@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "shopify_customer_id": "c1",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: initial message
        first = await client.post(
            "/chat",
            json={**base_payload, "message": "Where is my order?"},
        )
        assert first.status_code == 200
        first_data = first.json()
        assert first_data["agent"] == "wismo"
        assert first_data["state"]["last_assistant_message"] is not None

        # Turn 2: continuation (different message, same conversation)
        second = await client.post(
            "/chat",
            json={**base_payload, "message": "Thanks, that helps!"},
        )
        assert second.status_code == 200
        second_data = second.json()
        assert second_data["agent"] == "wismo"
        assert second_data["state"]["last_assistant_message"] is not None

        # Thread should have both exchanges: user, assistant, user, assistant
        thread_resp = await client.get(f"/thread/{conv_id}")
        assert thread_resp.status_code == 200
        thread = thread_resp.json()
        assert len(thread["messages"]) >= 4

        user_msgs = [m for m in thread["messages"] if m["role"] == "user"]
        assistant_msgs = [m for m in thread["messages"] if m["role"] == "assistant"]
        assert len(user_msgs) >= 2
        assert len(assistant_msgs) >= 2
        assert user_msgs[0]["content"] == "Where is my order?"
        assert user_msgs[1]["content"] == "Thanks, that helps!"
