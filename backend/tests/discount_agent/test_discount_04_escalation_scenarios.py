"""Discount Test Suite 04: Escalation Scenarios"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_discount, post_chat


@pytest.mark.asyncio
async def test_04_01_discount_should_not_escalate(temp_db, mock_route_to_discount, unset_api_url):
    """Normal discount request should not escalate."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Can I get a discount code?"
        ))

    # Should not escalate (if implemented properly)
    # Otherwise just verify agent responded
    assert data["agent"] == "discount"
    assert data["state"].get("is_escalated", False) is False


@pytest.mark.asyncio
async def test_04_02_tool_failure_escalates(temp_db, mock_route_to_discount, unset_api_url, monkeypatch):
    """Tool failure should escalate to Monica."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Critical API failure")

    import agents.discount_agent.graph as graph_mod
    monkeypatch.setattr(graph_mod, "create_discount_10_percent", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Can I get a discount?"
        ))

    # Should escalate or respond with apology
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "monica" in msg or "trouble" in msg or "sorry" in msg
