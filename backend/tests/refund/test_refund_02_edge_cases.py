"""Refund Test Suite 02: Edge Cases"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_refund, post_chat


@pytest.mark.asyncio
async def test_02_01_no_email_escalates(temp_db, mock_route_to_refund, unset_api_url):
    """Missing customer email should escalate."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            email="",
            message="I want a refund."
        ))

    assert data["state"]["is_escalated"] is True
    msg = (data["state"].get("last_assistant_message") or "").lower()
    assert "monica" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_02_02_unicode_customer_name(temp_db, mock_route_to_refund, unset_api_url):
    """Unicode in customer name should be handled."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(
            first_name="Müller",
            last_name="Žižek",
            message="Refund bitte. Die Patches funktionieren nicht."
        ))

    assert data["agent"] == "refund"
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_02_03_very_long_message(temp_db, mock_route_to_refund, unset_api_url):
    """Very long customer message should be handled."""
    from api.server import app

    long_message = (
        "I ordered the BuzzPatch for my three kids ages 5, 7, and 9 because we were going camping "
        "and I wanted to avoid using chemical sprays. We used the patches exactly as instructed—one "
        "on each child's clothes before going outside. Unfortunately, all three kids still got multiple "
        "mosquito bites during our camping trip. I'm really disappointed because I spent a lot of money "
        "on these patches and they simply didn't work. I would like a full refund please. " * 3
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(message=long_message))

    assert data["agent"] == "refund"
    assert data["state"]["last_assistant_message"] is not None


@pytest.mark.asyncio
async def test_02_04_empty_message(temp_db, mock_route_to_refund, unset_api_url):
    """Empty message should still get a response."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_refund(message=""))

    assert data["agent"] == "refund"
    # Should handle gracefully
    assert data["state"]["last_assistant_message"] is not None or data["state"]["is_escalated"]
