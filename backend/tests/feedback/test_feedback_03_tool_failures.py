"""Feedback Test Suite 03: Tool Failures"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_feedback, post_chat


@pytest.mark.asyncio
async def test_03_01_order_lookup_fails_still_responds(temp_db, mock_route_to_feedback, unset_api_url, monkeypatch):
    """Order lookup failure shouldn't stop warm response."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="API timeout")

    import agents.feedback.graph as graph_mod
    monkeypatch.setattr(graph_mod, "get_customer_latest_order", mock_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="Love the patches!"
        ))

    # Should still respond warmly even if tagging fails
    assert data["state"]["last_assistant_message"] is not None
    msg = data["state"].get("last_assistant_message") or ""
    assert any(emoji in msg for emoji in ["🥰", "🙏", "😊", "❤️"])


@pytest.mark.asyncio
async def test_03_02_tagging_fails_gracefully(temp_db, mock_route_to_feedback, unset_api_url, monkeypatch):
    """Tagging failure shouldn't break the response."""
    from api.server import app
    from schemas.internal import ToolResponse

    async def mock_tag_fail(*args, **kwargs):
        return ToolResponse(success=False, data={}, error="Tag API error")

    import agents.feedback.graph as graph_mod
    monkeypatch.setattr(graph_mod, "add_order_tags", mock_tag_fail, raising=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_feedback(
            message="Amazing patches!"
        ))

    # Should still respond
    assert data["state"]["last_assistant_message"] is not None
