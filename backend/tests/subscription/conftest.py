"""Shared fixtures for Subscription test suite."""

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
    """Create a temporary test database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        from core.database import Checkpointer
        cp = Checkpointer(db_path=path)
        monkeypatch.setattr("api.server.checkpointer", cp)
        yield cp
    finally:
        import os
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def mock_route_to_subscription(monkeypatch):
    """Force router to route to subscription agent."""
    async def _route(state):
        state["intent"] = "Subscription Management"
        state["routed_agent"] = "subscription"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    """Ensure API_URL is unset for mock mode."""
    monkeypatch.setenv("API_URL", "")


def payload_subscription(
    conv_id=None,
    email="subscriber@example.com",
    message="I want to manage my subscription.",
    first_name="Sarah",
    last_name="Customer",
    **kwargs
):
    """Build a subscription payload."""
    return {
        "conversation_id": conv_id or f"subscription-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-test"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": first_name,
        "last_name": last_name,
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-subscription"),
        "message": message,
    }


async def post_chat(client, payload):
    """POST to /chat endpoint."""
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()
