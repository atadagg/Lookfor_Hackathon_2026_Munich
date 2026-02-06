"""WISMO-specific composite tools.

These wrap the shared Shopify tool adapters with WISMO-specific logic:
- ``get_order_status`` — two-step lookup (customer orders → order details)
- ``get_order_by_id``  — direct order lookup by #id
- ``extract_order_id`` — regex extraction from free text

Mock behaviour (when API_URL is not set) is controlled by email:
    unfulfilled@test.com  →  UNFULFILLED
    delivered@test.com    →  DELIVERED
    noorders@test.com     →  no orders (triggers ask-for-order-ID)
    anything else         →  IN_TRANSIT with tracking URL
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from schemas.internal import ToolResponse
from tools.api import API_URL, post_tool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Mock scenarios (local dev / no API_URL) ────────────────────────

_MOCK_BY_EMAIL: Dict[str, Optional[Dict[str, Any]]] = {
    "unfulfilled@test.com": {
        "order_id": "#2001",
        "status": "UNFULFILLED",
        "tracking_url": None,
    },
    "delivered@test.com": {
        "order_id": "#3001",
        "status": "DELIVERED",
        "tracking_url": "https://tracking.example.com/delivered456",
    },
    "noorders@test.com": None,  # signals no orders
}

_DEFAULT_MOCK: Dict[str, Any] = {
    "order_id": "#1001",
    "status": "IN_TRANSIT",
    "tracking_url": "https://tracking.example.com/demo123",
}


# ── Public tools ───────────────────────────────────────────────────


async def get_order_status(*, email: str) -> ToolResponse:
    """Fetch the latest order status for a customer by email.

    Two-step call:
      1) ``shopify_get_customer_orders`` → list of orders
      2) ``shopify_get_order_details``   → details for the most recent

    Returns ``data.no_orders = True`` when the customer has no orders.
    """

    # ---- Real API path ------------------------------------------------
    if API_URL:
        orders_resp = await post_tool(
            "hackhaton/get_customer_orders",
            {"email": email, "after": "null", "limit": 10},
        )
        if orders_resp.success:
            data = orders_resp.data
            orders = data.get("orders") if isinstance(data, dict) else []
            if not orders:
                return ToolResponse(success=True, data={"no_orders": True})

            latest = orders[0]
            order_name = latest.get("name") or latest.get("id", "")
            # Ensure starts with #
            if not order_name.startswith("#"):
                order_name = "#%s" % order_name

            details_resp = await post_tool(
                "hackhaton/get_order_details",
                {"orderId": order_name},
            )
            if details_resp.success:
                d = details_resp.data if isinstance(details_resp.data, dict) else {}
                return ToolResponse(success=True, data={
                    "order_id": d.get("name") or order_name,
                    "order_gid": d.get("id", ""),
                    "status": (d.get("status") or "").upper(),
                    "created_at": d.get("createdAt") or _now_iso(),
                    "tracking_url": d.get("trackingUrl"),
                })

        if not orders_resp.success:
            return orders_resp
        return ToolResponse(success=True, data={"no_orders": True})

    # ---- Mock path (local dev) ----------------------------------------
    scenario = _MOCK_BY_EMAIL.get(email)
    if scenario is None and email in _MOCK_BY_EMAIL:
        return ToolResponse(success=True, data={"no_orders": True})

    mock = dict(scenario or _DEFAULT_MOCK)
    mock["created_at"] = _now_iso()
    return ToolResponse(success=True, data=mock)


async def get_order_by_id(*, order_id: str) -> ToolResponse:
    """Look up a specific order by its order ID (e.g. #43189)."""

    # Ensure starts with #
    if not order_id.startswith("#"):
        order_id = "#%s" % order_id.lstrip("#").strip()

    if API_URL:
        resp = await post_tool(
            "hackhaton/get_order_details",
            {"orderId": order_id},
        )
        if resp.success:
            d = resp.data if isinstance(resp.data, dict) else {}
            return ToolResponse(success=True, data={
                "order_id": d.get("name") or order_id,
                "order_gid": d.get("id", ""),
                "status": (d.get("status") or "").upper(),
                "created_at": d.get("createdAt") or _now_iso(),
                "tracking_url": d.get("trackingUrl"),
            })
        return resp

    # Mock: return IN_TRANSIT for any order ID
    return ToolResponse(success=True, data={
        "order_id": order_id,
        "status": "IN_TRANSIT",
        "created_at": _now_iso(),
        "tracking_url": "https://tracking.example.com/%s" % order_id.lstrip("#"),
    })


def extract_order_id(text: str) -> Optional[str]:
    """Extract an order number from free-text customer input."""

    patterns = [
        r"#(\d+)",
        r"NP(\d{4,})",
        r"(?:order|order\s*#?)\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return "#%s" % match.group(1)

    stripped = text.strip()
    if stripped.isdigit() and len(stripped) >= 3:
        return "#%s" % stripped

    return None


__all__ = ["get_order_status", "get_order_by_id", "extract_order_id"]
