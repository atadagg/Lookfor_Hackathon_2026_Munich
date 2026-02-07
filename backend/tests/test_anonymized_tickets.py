"""Tests using real anonymized support tickets.

Loads tickets from anonymized_tickets.json and runs the first customer message
through the /chat API. Validates that the system responds without crashing.

Run with: pytest tests/test_anonymized_tickets.py -v
  - With mocks (default): fast, no API key needed
  - With real LLM: set OPENAI_API_KEY; uses real router + agents

To run with real LLM against all tickets:
  OPENAI_API_KEY=sk-... pytest tests/test_anonymized_tickets.py -v -k "real_tickets"
"""

import json
import pathlib
import re
import sys
import tempfile
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TICKETS_JSON = pathlib.Path(__file__).resolve().parent / "anonymized_tickets.json"


def _parse_first_customer_message(conversation: str) -> str | None:
    """Extract the first customer message from the conversation string."""
    if not conversation:
        return None
    idx = conversation.find('Customer\'s message: "')
    if idx == -1:
        return None
    start = idx + len('Customer\'s message: "')
    # Find the earliest closing delimiter (before next message)
    end_agent = conversation.find('" Agent\'s message:', start)
    end_customer = conversation.find('" Customer\'s message:', start)
    ends = [e for e in (end_agent, end_customer) if e != -1]
    end = min(ends) if ends else len(conversation)
    return conversation[start:end].strip()


def _load_tickets(limit: int | None = None) -> list[dict]:
    """Load tickets from JSON, optionally limiting count."""
    data = json.loads(TICKETS_JSON.read_text())
    if limit:
        data = data[:limit]
    return data


def _ticket_to_payload(ticket: dict, conv_id: str) -> dict | None:
    """Convert a ticket to a chat payload. Returns None if no customer message."""
    msg = _parse_first_customer_message(ticket.get("conversation", ""))
    if not msg or len(msg) < 5:
        return None
    # Derive email from customerId for mock compatibility
    cust_id = ticket.get("customerId", "cust_anon")
    email = f"user_{cust_id.replace('cust_', '')}@example.com"
    return {
        "conversation_id": conv_id,
        "user_id": "test-real-tickets",
        "channel": "email",
        "customer_email": email,
        "first_name": "Customer",
        "last_name": "Test",
        "shopify_customer_id": cust_id,
        "message": msg[:2000],  # cap length
    }


@pytest.fixture
def temp_db(monkeypatch):
    """Use an isolated temp SQLite DB for each test."""
    import os

    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        from core.database import Checkpointer

        cp = Checkpointer(db_path=path)
        monkeypatch.setattr("api.server.checkpointer", cp)
        yield path
    finally:
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    """Ensure tools use mock path (no real API calls)."""
    monkeypatch.setenv("API_URL", "")


@pytest.fixture
def mock_router_and_agents(monkeypatch):
    """Mock router to always route to wismo, and mock WISMO LLM response."""

    async def _route(state):
        state["intent"] = "Shipping Delay"
        state["routed_agent"] = "wismo"
        return state

    class FakeMessage:
        content = "Thanks for reaching out. Your order is on the way."

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

    monkeypatch.setattr("api.server.route", _route, raising=True)
    monkeypatch.setattr("core.llm.get_async_openai_client", lambda: FakeClient(), raising=True)


@pytest.mark.asyncio
async def test_anonymized_tickets_smoke(temp_db, mock_router_and_agents):
    """Run first 10 real tickets through /chat with mocks. No crash = pass."""
    from api.server import app

    tickets = _load_tickets(limit=10)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i, ticket in enumerate(tickets):
            conv_id = f"real-ticket-{i}-{uuid.uuid4().hex[:8]}"
            payload = _ticket_to_payload(ticket, conv_id)
            if not payload:
                continue
            resp = await client.post("/chat", json=payload, timeout=30.0)
            assert resp.status_code == 200, f"Ticket {i} failed: {resp.text[:200]}"
            data = resp.json()
            assert "conversation_id" in data
            assert "agent" in data
            assert "state" in data


@pytest.mark.asyncio
@pytest.mark.skipif(
    not __import__("os").environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - use mocks or set key for real LLM test",
)
async def test_anonymized_tickets_real_llm(temp_db):
    """Run first 5 real tickets through /chat with REAL router + agents.

    Requires OPENAI_API_KEY. Slower. Use for manual validation.
    """
    from api.server import app

    tickets = _load_tickets(limit=5)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i, ticket in enumerate(tickets):
            conv_id = f"real-llm-{i}-{uuid.uuid4().hex[:8]}"
            payload = _ticket_to_payload(ticket, conv_id)
            if not payload:
                continue
            resp = await client.post("/chat", json=payload, timeout=60.0)
            assert resp.status_code == 200, f"Ticket {i} failed: {resp.text[:500]}"
            data = resp.json()
            assert data["conversation_id"] == conv_id
            assert data["agent"]  # some agent handled it
            assert data["state"].get("last_assistant_message") or data.get("state", {}).get(
                "escalation_summary"
            )


def test_parse_first_customer_message():
    """Sanity check for conversation parser."""
    conv = 'Customer\'s message: "Where is my order?" Agent\'s message: "Hi! Checking..."'
    assert _parse_first_customer_message(conv) == "Where is my order?"
    conv2 = 'Customer\'s message: "Hello" Customer\'s message: "Follow up" Agent\'s message: "..."'
    assert _parse_first_customer_message(conv2) == "Hello"
    assert _parse_first_customer_message("") is None
    assert _parse_first_customer_message("No customer here") is None
