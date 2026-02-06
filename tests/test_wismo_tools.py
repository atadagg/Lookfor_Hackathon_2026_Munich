"""Simple tests for WISMO tools.

Run with: pytest tests/test_wismo_tools.py -v

These tests use the mock path (no API_URL) — no network or real API needed.
"""

import asyncio
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.wismo.tools import extract_order_id, get_order_by_id, get_order_status


@pytest.mark.asyncio
async def test_get_order_status_default_mock():
    """Without API_URL, get_order_status returns mock IN_TRANSIT data."""
    resp = await get_order_status(email="any@test.com")
    assert resp.success is True
    assert resp.data.get("status") == "IN_TRANSIT"
    assert resp.data.get("order_id") == "#1001"
    assert "tracking.example.com" in (resp.data.get("tracking_url") or "")


@pytest.mark.asyncio
async def test_get_order_status_no_orders_mock():
    """noorders@test.com triggers no_orders response."""
    resp = await get_order_status(email="noorders@test.com")
    assert resp.success is True
    assert resp.data.get("no_orders") is True


@pytest.mark.asyncio
async def test_get_order_status_unfulfilled_mock():
    """unfulfilled@test.com returns UNFULFILLED status."""
    resp = await get_order_status(email="unfulfilled@test.com")
    assert resp.success is True
    assert resp.data.get("status") == "UNFULFILLED"
    assert resp.data.get("order_id") == "#2001"


@pytest.mark.asyncio
async def test_get_order_status_delivered_mock():
    """delivered@test.com returns DELIVERED status."""
    resp = await get_order_status(email="delivered@test.com")
    assert resp.success is True
    assert resp.data.get("status") == "DELIVERED"
    assert "delivered456" in (resp.data.get("tracking_url") or "")


@pytest.mark.asyncio
async def test_get_order_by_id_mock():
    """get_order_by_id returns mock data for any order ID."""
    resp = await get_order_by_id(order_id="#12345")
    assert resp.success is True
    assert resp.data.get("order_id") == "#12345"
    assert resp.data.get("status") == "IN_TRANSIT"


@pytest.mark.asyncio
async def test_get_order_by_id_normalizes_without_hash():
    """Order ID without # is normalized to include it."""
    resp = await get_order_by_id(order_id="9999")
    assert resp.success is True
    assert resp.data.get("order_id") == "#9999"


def test_extract_order_id_hash_format():
    """Extract order ID from #12345 format."""
    assert extract_order_id("my order #12345") == "#12345"
    assert extract_order_id("#99999") == "#99999"


def test_extract_order_id_np_format():
    """Extract order ID from NP format."""
    assert extract_order_id("order NP1234567") == "#1234567"


def test_extract_order_id_word_format():
    """Extract order ID from 'order 12345' format."""
    assert extract_order_id("order 43189") == "#43189"
    assert extract_order_id("Order #9876") == "#9876"


def test_extract_order_id_plain_digits():
    """Plain 3+ digit number is treated as order ID."""
    assert extract_order_id("12345") == "#12345"
    assert extract_order_id("  999  ") == "#999"


def test_extract_order_id_not_found():
    """Returns None when no order ID pattern matches."""
    assert extract_order_id("hello world") is None
    assert extract_order_id("12") is None  # too short
    assert extract_order_id("") is None
