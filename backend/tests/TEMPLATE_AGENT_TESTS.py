"""Template for Agent Test Suite

Copy this file to create comprehensive tests for other agents:
- wrong_item
- product_issue
- refund
- order_mod
- feedback
- subscription
- discount

Usage:
1. Copy this file to tests/[agent_name]/test_[agent_name]_01_basic_workflow.py
2. Replace [AGENT_NAME] with actual agent name (e.g., "wrong_item")
3. Replace [AGENT_CLASS] with actual agent class (e.g., "WrongItemAgent")
4. Replace [INTENT] with actual intent string
5. Update test cases to match agent's specific workflow
6. Repeat for 02_edge_cases, 03_tool_failures, etc.
"""

import pathlib
import sys
import tempfile
import uuid
from typing import Optional

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Shared Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def temp_db(monkeypatch):
    """Isolated temp SQLite DB for each test."""
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
def mock_route_to_[AGENT_NAME](monkeypatch):
    """Bypass real LLM router → always route to [AGENT_NAME]."""
    async def _route(state):
        state["intent"] = "[INTENT]"
        state["routed_agent"] = "[AGENT_NAME]"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_[AGENT_NAME]_llm(monkeypatch):
    """Mock the LLM in generate_response so tests don't need API keys."""
    class FakeMessage:
        content = "Mock response from customer support."
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
    """Force mock tool path (no real Shopify/Skio calls)."""
    monkeypatch.setenv("API_URL", "")


# ── Helper Functions ────────────────────────────────────────────────────────


def _payload(
    conv_id: Optional[str] = None,
    email: str = "test@example.com",
    message: str = "[SAMPLE_MESSAGE]",
    first_name: str = "Jane",
    last_name: str = "Doe",
    **kwargs
) -> dict:
    """Create a standard chat payload."""
    return {
        "conversation_id": conv_id or f"[agent]-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-test"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": first_name,
        "last_name": last_name,
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-test"),
        "message": message,
    }


async def _post_chat(client: AsyncClient, payload: dict) -> dict:
    """POST to /chat and assert success."""
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


async def _get_thread(client: AsyncClient, conv_id: str) -> dict:
    """GET thread details."""
    resp = await client.get(f"/thread/{conv_id}")
    assert resp.status_code == 200
    return resp.json()


# ── Test 01.01: Basic Workflow - [DESCRIBE FIRST WORKFLOW STEP] ────────────


@pytest.mark.asyncio
async def test_01_01_[workflow_step](temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """[DESCRIBE WHAT THIS TEST VERIFIES]"""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message="[SAMPLE_MESSAGE]"))

    assert data["agent"] == "[AGENT_NAME]"
    st = data["state"]
    assert st["routed_agent"] == "[AGENT_NAME]"
    assert st["current_workflow"] == "[WORKFLOW_NAME]"
    assert st["is_escalated"] is False
    # Add agent-specific assertions here


# ── Test 01.02: Basic Workflow - [DESCRIBE SECOND WORKFLOW STEP] ────────────


@pytest.mark.asyncio
async def test_01_02_[workflow_step](temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """[DESCRIBE WHAT THIS TEST VERIFIES]"""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message="[SAMPLE_MESSAGE]"))

    assert data["agent"] == "[AGENT_NAME]"
    # Add agent-specific assertions here


# ── Test 02.01: Edge Case - Missing Customer Email ─────────────────────────


@pytest.mark.asyncio
async def test_02_01_missing_email_handled(temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """Empty customer_email should be handled gracefully."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    # Should either escalate or handle gracefully
    assert data["state"]["is_escalated"] in (True, False)
    assert data["agent"] in ("[AGENT_NAME]", "escalated")


# ── Test 03.01: Tool Failure - [TOOL_NAME] failure escalates ────────────────


@pytest.mark.asyncio
async def test_03_01_[tool_name]_failure_escalates(temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """When [TOOL_NAME] returns success=false, should escalate."""
    from schemas.internal import ToolResponse
    from agents.[agent_name] import tools

    # Patch tool to return failure
    original = tools.[tool_function]
    async def failing_[tool_function](*args, **kwargs):
        return ToolResponse(
            success=False,
            data={},
            error="[ERROR_MESSAGE]"
        )

    tools.[tool_function] = failing_[tool_function]

    try:
        from api.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = await _post_chat(client, _payload())

        assert data["state"]["is_escalated"] is True
    finally:
        tools.[tool_function] = original


# ── Test 04.01: Escalation - [ESCALATION_SCENARIO] ──────────────────────────


@pytest.mark.asyncio
async def test_04_01_[escalation_scenario]_escalates(temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """[DESCRIBE ESCALATION SCENARIO]"""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message="[TRIGGER_MESSAGE]"))

    assert data["state"]["is_escalated"] is True
    assert "monica" in data["state"]["last_assistant_message"].lower()


# ── Test 05.01: Multi-Turn - Memory Preserved ──────────────────────────────


@pytest.mark.asyncio
async def test_05_01_multiturn_memory_preserved(temp_db, mock_route_to_[AGENT_NAME], mock_[AGENT_NAME]_llm):
    """Multiple turns in same thread → all messages preserved."""
    from api.server import app

    conv_id = f"[agent]-mem-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "[MESSAGE_1]"})
        await _post_chat(client, {**base, "message": "[MESSAGE_2]"})

        thread = await _get_thread(client, conv_id)

    assert len(thread["messages"]) >= 4  # 2 user + 2 assistant


# ── Test 09.01: Real LLM Integration ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_09_01_real_llm_routes_correctly(temp_db):
    """Real GPT-4o-mini should classify intent correctly."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message="[SAMPLE_MESSAGE]"))

    assert data["agent"] == "[AGENT_NAME]"
    assert data["state"]["routed_agent"] == "[AGENT_NAME]"
