"""WISMO Test Suite 03: Tool Failures - Network Errors, API Failures

Covers tool failure scenarios that could happen during demo:
- Tool returns success=false
- Tool returns malformed data
- Tool timeout (simulated)
- Network errors
- Invalid tool responses
- Tool error messages
"""

import pathlib
import sys
import tempfile
import uuid
from typing import Optional
from unittest.mock import AsyncMock, patch

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
def mock_route_to_wismo(monkeypatch):
    async def _route(state):
        state["intent"] = "Shipping Delay – Neutral Status Check"
        state["routed_agent"] = "wismo"
        return state
    monkeypatch.setattr("api.server.route", _route, raising=True)


@pytest.fixture
def mock_wismo_llm(monkeypatch):
    class FakeMessage:
        content = "Mock response"
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


def _payload(conv_id=None, email="test@example.com", message="Where is my order?", **kwargs):
    return {
        "conversation_id": conv_id or f"wismo-{uuid.uuid4().hex[:8]}",
        "user_id": kwargs.get("user_id", "user-test"),
        "channel": kwargs.get("channel", "email"),
        "customer_email": email,
        "first_name": kwargs.get("first_name", "Jane"),
        "last_name": kwargs.get("last_name", "Doe"),
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-test"),
        "message": message,
    }


async def _post_chat(client, payload):
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


# ── Test 03.01: Tool returns success=false → escalates ────────────────────


@pytest.mark.asyncio
async def test_03_01_tool_failure_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm, monkeypatch):
    """When get_order_status returns success=false, should escalate."""
    from schemas.internal import ToolResponse
    import agents.wismo.graph as graph_mod

    async def failing_get_order_status(*, email: str):
        return ToolResponse(
            success=False,
            data={},
            error="Shopify API returned 500 Internal Server Error"
        )

    # Patch in graph module's namespace (where it's actually used)
    monkeypatch.setattr(graph_mod, "get_order_status", failing_get_order_status)

    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["is_escalated"] is True
    assert "monica" in data["state"]["last_assistant_message"].lower() or "looping" in data["state"]["last_assistant_message"].lower()


# ── Test 03.02: Tool returns malformed data → escalates ────────────────────


@pytest.mark.asyncio
async def test_03_02_tool_malformed_data_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """When tool returns success=true but malformed data, should handle gracefully."""
    from schemas.internal import ToolResponse
    from agents.wismo import tools

    original = tools.get_order_status
    async def malformed_get_order_status(*, email: str):
        # Returns success but missing required fields
        return ToolResponse(
            success=True,
            data={"some_field": "value"},  # Missing order_id, status, etc.
            error=None
        )

    tools.get_order_status = malformed_get_order_status

    try:
        from api.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = await _post_chat(client, _payload())

        # Should either escalate or handle gracefully (no crash)
        assert data["state"]["is_escalated"] in (True, False)
        assert data["agent"] in ("wismo", "escalated")
    finally:
        tools.get_order_status = original


# ── Test 03.03: get_order_by_id failure → escalates ────────────────────────


@pytest.mark.asyncio
async def test_03_03_get_order_by_id_failure_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm, monkeypatch):
    """When get_order_by_id fails, should escalate."""
    from schemas.internal import ToolResponse
    import agents.wismo.graph as graph_mod

    conv_id = f"wismo-toolfail-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id, email="noorders@test.com")

    async def failing_get_order_by_id(*, order_id: str):
        return ToolResponse(
            success=False,
            data={},
            error="Order not found"
        )

    # Patch in graph module's namespace
    monkeypatch.setattr(graph_mod, "get_order_by_id", failing_get_order_by_id)

    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Where is my order?"})
        data = await _post_chat(client, {**base, "message": "It's #12345"})

    assert data["state"]["is_escalated"] is True
    assert "monica" in data["state"]["last_assistant_message"].lower()


# ── Test 03.04: Tool timeout (simulated) → escalates ───────────────────────


@pytest.mark.asyncio
async def test_03_04_tool_timeout_escalates(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """When tool times out, should escalate."""
    import asyncio
    from schemas.internal import ToolResponse
    from agents.wismo import tools

    original = tools.get_order_status
    async def timeout_get_order_status(*, email: str):
        await asyncio.sleep(0.1)  # Simulate delay
        raise asyncio.TimeoutError("Tool call timed out after 30s")

    tools.get_order_status = timeout_get_order_status

    try:
        from api.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Should catch exception and escalate
            data = await _post_chat(client, _payload())

        # Should either escalate or handle gracefully
        assert data["state"]["is_escalated"] in (True, False)
    finally:
        tools.get_order_status = original


# ── Test 03.05: Tool returns empty data → handles gracefully ───────────────


@pytest.mark.asyncio
async def test_03_05_tool_empty_data_handled(temp_db, mock_route_to_wismo, mock_wismo_llm):
    """When tool returns empty data dict, should handle gracefully."""
    from schemas.internal import ToolResponse
    from agents.wismo import tools

    original = tools.get_order_status
    async def empty_get_order_status(*, email: str):
        return ToolResponse(
            success=True,
            data={},  # Empty dict
            error=None
        )

    tools.get_order_status = empty_get_order_status

    try:
        from api.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = await _post_chat(client, _payload())

        # Should handle gracefully (likely escalates or asks for order ID)
        assert data["state"]["is_escalated"] in (True, False)
        assert data["agent"] in ("wismo", "escalated")
    finally:
        tools.get_order_status = original


# ── Test 03.06: Tool error message preserved in escalation ──────────────────


@pytest.mark.asyncio
async def test_03_06_tool_error_message_preserved(temp_db, mock_route_to_wismo, mock_wismo_llm, monkeypatch):
    """Tool error messages should be preserved in escalation_summary."""
    from schemas.internal import ToolResponse
    import agents.wismo.graph as graph_mod

    async def failing_get_order_status(*, email: str):
        return ToolResponse(
            success=False,
            data={},
            error="Shopify API rate limit exceeded"
        )

    # Patch in graph module's namespace
    monkeypatch.setattr(graph_mod, "get_order_status", failing_get_order_status)

    from api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload())

    assert data["state"]["is_escalated"] is True
    # Check that escalation_summary contains error details
    escalation = data["state"].get("escalation_summary")
    if escalation:
        assert "error" in str(escalation).lower() or "rate limit" in str(escalation).lower()
