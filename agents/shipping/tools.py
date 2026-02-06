"""Tools for the Shipping (WISMO) specialist.

These are **Python adapters** around the hackathon tooling API. During
local development they can fall back to deterministic mocks, but in the
evaluation environment they should call the real HTTP endpoints.

All functions must return ``ToolResponse`` to match the uniform contract.

Mock behaviour
--------------
When ``API_URL`` is not set, responses are controlled by the
``shopify_customer_id`` passed in:

    cust-unfulfilled  →  UNFULFILLED (no tracking)
    cust-delivered    →  DELIVERED
    cust-no-orders    →  empty order list  (triggers "ask for order ID")
    anything else     →  IN_TRANSIT with tracking URL
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from schemas.internal import ToolResponse


API_URL = os.environ.get("API_URL", "").rstrip("/")


# ── Low-level HTTP helper ──────────────────────────────────────────


async def _post_tool(path: str, payload: Dict[str, Any]) -> ToolResponse:
    """Call a hackathon tool endpoint and normalise the response."""

    if not API_URL:
        return ToolResponse(success=False, error="API_URL is not configured.")

    url = "%s/%s" % (API_URL, path.lstrip("/"))

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
    except Exception as exc:
        return ToolResponse(success=False, error="HTTP error calling %s: %s" % (url, exc))

    if resp.status_code != 200:
        return ToolResponse(
            success=False,
            error="Non-200 status from %s: %s" % (url, resp.status_code),
        )

    try:
        body = resp.json()
    except Exception as exc:
        return ToolResponse(success=False, error="Invalid JSON from %s: %s" % (url, exc))

    if not isinstance(body, dict):
        return ToolResponse(success=False, error="Unexpected response shape from %s" % url)

    success = bool(body.get("success"))
    data = body.get("data") or {}
    error = body.get("error")

    if not success and not error:
        error = "Tool call failed without error message."
    if not isinstance(data, dict):
        data = {}

    return ToolResponse(success=success, data=data, error=error)


# ── Mock scenarios (local dev / no API_URL) ────────────────────────

_MOCK_SCENARIOS: Dict[str, Optional[Dict[str, Any]]] = {
    "cust-unfulfilled": {
        "order_id": "#2001",
        "status": "UNFULFILLED",
        "created_at": datetime.utcnow().isoformat(),
        "tracking_url": None,
        "raw": {},
    },
    "cust-delivered": {
        "order_id": "#3001",
        "status": "DELIVERED",
        "created_at": datetime.utcnow().isoformat(),
        "tracking_url": "https://tracking.example.com/delivered456",
        "raw": {},
    },
    "cust-no-orders": None,  # signals: no orders found
}

_DEFAULT_MOCK: Dict[str, Any] = {
    "order_id": "#1001",
    "status": "IN_TRANSIT",
    "created_at": datetime.utcnow().isoformat(),
    "tracking_url": "https://tracking.example.com/demo123",
    "raw": {},
}


# ── Public tools ───────────────────────────────────────────────────


async def get_order_status(*, shopify_customer_id: str) -> ToolResponse:
    """Fetch the latest order status for a Shopify customer.

    Two-step call mirroring the tooling spec:
      1) ``shopify_get_customer_orders``  →  list of orders
      2) ``shopify_get_order_details``    →  details for the most recent

    Returns ``data.no_orders = True`` when the customer has no orders.
    """

    # ---- Real API path ------------------------------------------------
    if API_URL:
        orders_resp = await _post_tool(
            "shopify_get_customer_orders",
            {"shopifyCustomerId": shopify_customer_id},
        )
        if orders_resp.success:
            orders = orders_resp.data.get("orders") or []
            if not orders:
                return ToolResponse(success=True, data={"no_orders": True})

            latest = orders[0]
            order_id = latest.get("id") or latest.get("order_id")
            if order_id:
                details_resp = await _post_tool(
                    "shopify_get_order_details",
                    {"orderId": order_id},
                )
                if details_resp.success:
                    data = details_resp.data
                    normalised: Dict[str, Any] = {
                        "order_id": data.get("order_id") or "#%s" % order_id,
                        "status": (data.get("status") or "").upper(),
                        "created_at": data.get("created_at")
                        or datetime.utcnow().isoformat(),
                        "tracking_url": data.get("tracking_url"),
                        "raw": data,
                    }
                    return ToolResponse(success=True, data=normalised)

        if not orders_resp.success:
            return orders_resp

        # API returned success but empty — signal no orders
        return ToolResponse(success=True, data={"no_orders": True})

    # ---- Mock path (local dev) ----------------------------------------
    scenario = _MOCK_SCENARIOS.get(shopify_customer_id)
    if scenario is None and shopify_customer_id in _MOCK_SCENARIOS:
        # Explicit None → no orders
        return ToolResponse(success=True, data={"no_orders": True})

    mock_data = dict(scenario or _DEFAULT_MOCK)
    mock_data["created_at"] = datetime.utcnow().isoformat()
    return ToolResponse(success=True, data=mock_data)


async def get_order_by_id(*, order_id: str) -> ToolResponse:
    """Look up a specific order by its order ID.

    Used when the customer provides an order number after the initial
    lookup found nothing under their Shopify customer ID.
    """

    clean_id = order_id.lstrip("#").strip()

    if API_URL:
        resp = await _post_tool(
            "shopify_get_order_details",
            {"orderId": clean_id},
        )
        if resp.success:
            data = resp.data
            return ToolResponse(
                success=True,
                data={
                    "order_id": data.get("order_id") or "#%s" % clean_id,
                    "status": (data.get("status") or "").upper(),
                    "created_at": data.get("created_at")
                    or datetime.utcnow().isoformat(),
                    "tracking_url": data.get("tracking_url"),
                    "raw": data,
                },
            )
        return resp

    # Mock: return IN_TRANSIT for any order ID in local dev
    return ToolResponse(
        success=True,
        data={
            "order_id": "#%s" % clean_id,
            "status": "IN_TRANSIT",
            "created_at": datetime.utcnow().isoformat(),
            "tracking_url": "https://tracking.example.com/%s" % clean_id,
            "raw": {},
        },
    )


async def get_tracking_link(*, order_id: str) -> ToolResponse:
    """Return a tracking link for the given order id."""

    return ToolResponse(
        success=True,
        data={
            "order_id": order_id,
            "tracking_url": "https://tracking.example.com/%s" % order_id.lstrip("#"),
        },
    )


def extract_order_id(text: str) -> Optional[str]:
    """Try to pull an order number from free-text customer input.

    Looks for patterns like ``#12345``, ``NP1234567``,
    ``order 12345``, or a bare number.
    """

    patterns = [
        r"#(\d+)",
        r"NP(\d{4,})",
        r"(?:order|order\s*#?)\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            digits = match.group(1)
            return "#%s" % digits

    # Bare number as the whole message
    stripped = text.strip()
    if stripped.isdigit() and len(stripped) >= 3:
        return "#%s" % stripped

    return None


__all__ = [
    "get_order_status",
    "get_order_by_id",
    "get_tracking_link",
    "extract_order_id",
]
