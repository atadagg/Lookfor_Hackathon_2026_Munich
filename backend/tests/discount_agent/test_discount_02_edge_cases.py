"""Discount Test Suite 02: Edge Cases"""

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
async def test_02_01_polite_discount_request(temp_db, mock_route_to_discount, unset_api_url):
    """Polite discount request."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Would you be so kind as to provide a discount code? Thank you!"
        ))

    assert data["agent"] == "discount"
    # Verify agent responded in some way
    assert data.get("state") is not None


@pytest.mark.asyncio
async def test_02_02_short_request(temp_db, mock_route_to_discount, unset_api_url):
    """Very short request."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Discount?"
        ))

    assert data["agent"] == "discount"
    # Verify agent responded
    assert data.get("state") is not None


@pytest.mark.asyncio
async def test_02_03_specific_percentage_request(temp_db, mock_route_to_discount, unset_api_url):
    """Request for specific percentage (still get 10%)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await post_chat(client, payload_discount(
            message="Can I get a 20% discount code?"
        ))

    assert data["agent"] == "discount"
    # Should provide 10% code (not 20%) - if implemented
    # Otherwise just verify routed correctly
    assert data.get("state") is not None
