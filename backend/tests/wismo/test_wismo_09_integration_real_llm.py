"""WISMO Test Suite 09: Integration Tests with Real LLM

These tests use REAL OpenAI API calls (router + response generation).
Only Shopify/Skio endpoints are mocked (via empty API_URL).

Requires: OPENAI_API_KEY in backend/.env

Run with: pytest tests/wismo/test_wismo_09_integration_real_llm.py -v
"""

import os
import pathlib
import sys
import tempfile
import uuid
from datetime import date, timedelta
from typing import Optional

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

_has_api_key = bool(os.getenv("OPENAI_API_KEY"))
pytestmark = pytest.mark.skipif(
    not _has_api_key, reason="OPENAI_API_KEY not set – skipping integration tests"
)


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


@pytest.fixture(autouse=True)
def use_mock_tools(monkeypatch):
    monkeypatch.setenv("API_URL", "")


@pytest.fixture(autouse=True)
def reset_llm_clients():
    import core.llm as llm_mod
    import router.logic as router_mod
    old_llm = llm_mod._async_client
    old_router = router_mod._client
    llm_mod._async_client = None
    router_mod._client = None
    yield
    llm_mod._async_client = old_llm
    router_mod._client = old_router


def _payload(conv_id=None, email="test@example.com", message="Where is my order?", **kwargs):
    return {
        "conversation_id": conv_id or f"int-wismo-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-int"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": kwargs.get("first_name", "Jane"),
        "last_name": kwargs.get("last_name", "Doe"),
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-int"),
        "message": message,
    }


async def _post_chat(client, payload):
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


# ── Test 09.01: Real LLM routes shipping query correctly ────────────────────


@pytest.mark.asyncio
async def test_09_01_real_llm_routes_shipping(temp_db):
    """Real GPT-4o-mini should classify shipping delay → wismo."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Order #43189 shows 'in transit' for 10 days. Any update?")
        )

    assert data["agent"] == "wismo"
    assert data["state"]["routed_agent"] == "wismo"


# ── Test 09.02: Real LLM generates meaningful response ──────────────────────


@pytest.mark.asyncio
async def test_09_02_real_llm_generates_response(temp_db):
    """Real GPT-4o-mini should compose a natural response."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Hi, just curious when my BuzzPatch will arrive to Toronto.")
        )

    reply = data["state"]["last_assistant_message"]
    assert reply is not None and len(reply) > 20
    reply_lower = reply.lower()
    has_relevant = any(
        t in reply_lower for t in ["transit", "on the way", "tracking", "shipped", "delivery", "arrive", "wait", "friday", "next week"]
    )
    assert has_relevant, f"LLM response doesn't mention order status: {reply}"


# ── Test 09.03: Full flow with real LLM ─────────────────────────────────────


@pytest.mark.asyncio
async def test_09_03_full_flow_real_llm(temp_db):
    """Complete flow: real router + real LLM + real graph."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Can you confirm the estimated delivery date? Thanks!")
        )

    assert data["agent"] == "wismo"
    st = data["state"]
    assert st["workflow_step"] == "wait_promise_set"
    assert len(st["internal_data"]["tool_traces"]) >= 1
    assert st["last_assistant_message"] is not None and len(st["last_assistant_message"]) > 30
