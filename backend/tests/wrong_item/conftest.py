"""Shared fixtures for Wrong Item test suite."""

import pathlib
import sys
import tempfile
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

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
        import os
        try:
            os.close(fd)
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def mock_route_to_wrong_item(monkeypatch):
    async def _route(state):
        state["intent"] = "Wrong / Missing Item in Parcel"
        state["routed_agent"] = "wrong_item"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture(autouse=True)
def unset_api_url(monkeypatch):
    monkeypatch.setenv("API_URL", "")


def payload_wrong_item(
    conv_id=None,
    email="lisa@example.com",
    message="Got Zen stickers instead of Focus—kids need them for school, help!",
    first_name="Lisa",
    last_name="Green",
    **kwargs
):
    return {
        "conversation_id": conv_id or f"wrong-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-test"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": first_name,
        "last_name": last_name,
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-200"),
        "message": message,
    }


async def post_chat(client, payload):
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()
