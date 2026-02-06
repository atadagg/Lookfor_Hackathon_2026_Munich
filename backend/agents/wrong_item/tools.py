"""Wrong-item composite tools.

Composes root Shopify tools for the Wrong/Missing Item workflow:
- get_orders_and_details — orders by email + latest order details (incl. line items)
- get_order_by_id      — order details by order ID
- extract_order_id     — regex from free text
- add_order_tags       — thin wrapper over shopify_add_tags
- create_store_credit  — thin wrapper over shopify_create_store_credit
- refund_order_cash    — thin wrapper over shopify_refund_order

Mock behaviour (when API_URL is not set) is keyed by email:
  noorders@test.com  →  no orders (ask for order ID)
  else               →  one order with id, gid, line_items, customer_gid
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from schemas.internal import ToolResponse
from tools.api import API_URL
from tools.shopify import (
    shopify_add_tags,
    shopify_create_store_credit,
    shopify_get_customer_orders,
    shopify_get_order_details,
    shopify_refund_order,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _details_to_wrong_item_format(
    d: Dict[str, Any], order_name: str, order_gid: str = ""
) -> Dict[str, Any]:
    """Map Shopify order details to wrong-item format (order_id, order_gid, line_items, customer_gid)."""
    gid = d.get("id") or order_gid or "gid://shopify/Order/5531567751245"
    line_items_raw = d.get("lineItems") or d.get("line_items") or []
    line_items: List[Dict[str, Any]] = []
    for li in line_items_raw if isinstance(line_items_raw, list) else []:
        if isinstance(li, dict):
            line_items.append({
                "title": li.get("title", ""),
                "fulfilled": li.get("fulfilled", True),
                "quantity": li.get("quantity", 1),
            })
        else:
            line_items.append({"title": str(li), "fulfilled": True, "quantity": 1})
    if not line_items and d.get("name"):
        line_items = [{"title": "Order %s" % order_name, "fulfilled": True, "quantity": 1}]
    return {
        "order_id": d.get("name") or order_name,
        "order_gid": gid,
        "customer_gid": d.get("customerId") or d.get("customer_id") or "gid://shopify/Customer/200",
        "line_items": line_items,
        "created_at": d.get("createdAt") or _now_iso(),
        "status": (d.get("status") or "FULFILLED").upper(),
    }


# ── Mock scenarios (no API_URL) ─────────────────────────────────────

_MOCK_NO_ORDERS_EMAILS = frozenset({"noorders@test.com"})

_DEFAULT_MOCK_ORDER: Dict[str, Any] = {
    "order_id": "#1001",
    "order_gid": "gid://shopify/Order/5531567751245",
    "customer_gid": "gid://shopify/Customer/200",
    "line_items": [
        {"title": "Focus Stickers", "fulfilled": True, "quantity": 1},
        {"title": "Zen Stickers", "fulfilled": True, "quantity": 1},
    ],
    "created_at": None,
    "status": "FULFILLED",
}


# ── Public tools ────────────────────────────────────────────────────


async def get_orders_and_details(*, email: str) -> ToolResponse:
    """Fetch customer orders and latest order details (incl. line items) by email.

    Composes: shopify_get_customer_orders → shopify_get_order_details.
    Returns data.no_orders = True when the customer has no orders.
    """
    if not API_URL:
        if email in _MOCK_NO_ORDERS_EMAILS:
            return ToolResponse(success=True, data={"no_orders": True})
        mock = dict(_DEFAULT_MOCK_ORDER)
        mock["created_at"] = _now_iso()
        return ToolResponse(success=True, data=mock)

    orders_result = await shopify_get_customer_orders(
        email=email, after="null", limit=10
    )
    if not orders_result.get("success"):
        return ToolResponse(
            success=False,
            data={},
            error=orders_result.get("error", "Order lookup failed"),
        )
    data = orders_result.get("data") or {}
    orders = data.get("orders", []) if isinstance(data, dict) else []
    if not orders:
        return ToolResponse(success=True, data={"no_orders": True})

    latest = orders[0]
    order_name = latest.get("name") or latest.get("id") or ""
    if order_name and not order_name.startswith("#"):
        order_name = "#%s" % order_name
    order_gid = latest.get("id", "")

    details_result = await shopify_get_order_details(orderId=order_name)
    if not details_result.get("success"):
        return ToolResponse(
            success=False,
            data={},
            error=details_result.get("error", "Order details lookup failed"),
        )
    d = details_result.get("data") or {}
    if not isinstance(d, dict):
        d = {}
    out = _details_to_wrong_item_format(d, order_name, order_gid)
    return ToolResponse(success=True, data=out)


async def get_order_by_id(*, order_id: str) -> ToolResponse:
    """Look up order details by order ID (e.g. #43189)."""
    if not order_id.startswith("#"):
        order_id = "#%s" % order_id.lstrip("#").strip()

    if not API_URL:
        mock = dict(_DEFAULT_MOCK_ORDER)
        mock["order_id"] = order_id
        mock["order_gid"] = "gid://shopify/Order/%s" % order_id.lstrip("#")
        mock["created_at"] = _now_iso()
        return ToolResponse(success=True, data=mock)

    result = await shopify_get_order_details(orderId=order_id)
    if not result.get("success"):
        return ToolResponse(
            success=False,
            data={},
            error=result.get("error", "Order lookup failed"),
        )
    d = result.get("data") or {}
    if not isinstance(d, dict):
        d = {}
    out = _details_to_wrong_item_format(d, order_id)
    return ToolResponse(success=True, data=out)


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


async def add_order_tags(*, order_gid: str, tags: List[str]) -> ToolResponse:
    """Add tags to an order (e.g. Wrong or Missing, Store Credit Issued)."""
    if not tags:
        return ToolResponse(success=True, data={})
    result = await shopify_add_tags(id=order_gid, tags=tags)
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Add tags failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


async def create_store_credit(
    *,
    customer_gid: str,
    amount: str,
    currency_code: str = "USD",
    expires_at: Optional[str] = None,
) -> ToolResponse:
    """Issue store credit to the customer (e.g. item value + 10% bonus)."""
    credit_amount = {"amount": amount, "currencyCode": currency_code}
    result = await shopify_create_store_credit(
        id=customer_gid,
        creditAmount=credit_amount,
        expiresAt=expires_at,
    )
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Create store credit failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


async def refund_order_cash(*, order_gid: str) -> ToolResponse:
    """Refund order to original payment method."""
    result = await shopify_refund_order(
        orderId=order_gid,
        refundMethod="ORIGINAL_PAYMENT_METHODS",
    )
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Refund failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


__all__ = [
    "get_orders_and_details",
    "get_order_by_id",
    "extract_order_id",
    "add_order_tags",
    "create_store_credit",
    "refund_order_cash",
]
