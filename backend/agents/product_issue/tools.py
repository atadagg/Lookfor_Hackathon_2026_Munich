"""Product Issue – No Effect composite tools.

Composes shared Shopify tools for order/product lookup:
- ``get_order_and_product`` — shopify_get_customer_orders → shopify_get_order_details
  Returns order_id, order_gid for use by the graph.

Uses module reference (tools.shopify) so monkeypatching works in tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from schemas.internal import ToolResponse
from tools import shopify


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _details_to_product_issue_format(d: Dict[str, Any], order_name: str) -> Dict[str, Any]:
    """Map Shopify order details to product_issue internal format."""
    return {
        "order_id": d.get("name") or order_name,
        "order_gid": d.get("id", ""),
        "status": (d.get("status") or "").upper(),
        "created_at": d.get("createdAt") or _now_iso(),
    }


async def get_order_and_product(*, email: str) -> ToolResponse:
    """Fetch the latest order for a customer by email.

    Composes:
      1) shopify_get_customer_orders → list of orders
      2) shopify_get_order_details   → details for the most recent

    Returns ToolResponse with data.order_id, data.order_gid.
    Returns data.no_orders=True when the customer has no orders.
    """
    orders_result = await shopify.shopify_get_customer_orders(
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
    order_name = latest.get("name") or latest.get("id", "")
    if not order_name.startswith("#"):
        order_name = "#%s" % order_name

    details_result = await shopify.shopify_get_order_details(orderId=order_name)
    if not details_result.get("success"):
        return ToolResponse(
            success=False,
            data={},
            error=details_result.get("error", "Order details lookup failed"),
        )

    d = details_result.get("data") or {}
    if not isinstance(d, dict):
        d = {}
    payload = _details_to_product_issue_format(d, order_name)
    return ToolResponse(success=True, data=payload)


__all__ = ["get_order_and_product"]
