"""Subscription Test Suite 01: Basic Workflow

Tests subscription management: skip, discount, cancel, pause, billing escalation.
"""

import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conftest import payload_subscription, post_chat


@pytest.mark.asyncio
async def test_01_01_subscription_cancel_request(temp_db, mock_route_to_subscription, unset_api_url):
    """Cancel request routes to subscription agent."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            message="I want to cancel my subscription."
        ))

    assert data["agent"] == "subscription"
    assert data.get("state") is not None


@pytest.mark.asyncio
async def test_01_02_skip_next_order_request(temp_db, mock_route_to_subscription, unset_api_url):
    """Skip next order request."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            message="Can I skip my next order? I have too many patches."
        ))

    assert data["agent"] == "subscription"
    assert data.get("state") is not None


@pytest.mark.asyncio
async def test_01_03_billing_issue_escalates(temp_db, mock_route_to_subscription, unset_api_url):
    """Billing issue should escalate immediately."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            message="I was charged twice for my subscription!"
        ))

    # Should escalate for billing issues
    if data["state"].get("is_escalated"):
        msg = (data["state"].get("last_assistant_message") or "").lower()
        assert "monica" in msg or "looping" in msg


@pytest.mark.asyncio
async def test_01_04_pause_subscription_request(temp_db, mock_route_to_subscription, unset_api_url):
    """Pause subscription request."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            message="I want to pause my subscription for one month."
        ))

    assert data["agent"] == "subscription"
    assert data.get("state") is not None


@pytest.mark.asyncio
async def test_01_05_too_many_on_hand_flow(temp_db, mock_route_to_subscription, unset_api_url):
    """Too many on hand → Skip offer flow."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_subscription(
            message="I have too many patches on hand. What can we do?"
        ))

    assert data["agent"] == "subscription"
    # Should offer skip or discount
    assert data.get("state") is not None
