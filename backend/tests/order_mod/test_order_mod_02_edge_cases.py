"""Order Mod Test Suite 02: Edge Cases"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_order_mod, post_chat


@pytest.mark.asyncio
async def test_02_01_no_email_escalates(temp_db, mock_route_to_order_mod, unset_api_url):
    """Missing customer email should escalate."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            email="",
            message="Cancel my order."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "monica" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_02_02_ambiguous_request(temp_db, mock_route_to_order_mod, unset_api_url):
    """Ambiguous request should ask for clarification."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            message="I need to change something about my order."
        ))

    assert data["agent"] == "order_mod"
    # Should ask what they want to change
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_02_03_unicode_handling(temp_db, mock_route_to_order_mod, unset_api_url):
    """Unicode characters should be handled."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_order_mod(
            first_name="François",
            message="Je voudrais annuler ma commande. Merci! 🙏"
        ))

    assert data["agent"] == "order_mod"
    assert data["state"]["last_assistant_message"] is not None
