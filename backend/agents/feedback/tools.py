"""Feedback agent composite tools.

Wraps shopify tools for order lookup and tagging.
"""

from __future__ import annotations

from typing import List

from schemas.internal import ToolResponse
from tools.shopify import shopify_add_tags, shopify_get_customer_orders


async def get_customer_latest_order(*, email: str) -> ToolResponse:
    """Get the latest order for a customer by email."""
    result = await shopify_get_customer_orders(email=email, after="null", limit=10)
    if not result.get("success"):
        return ToolResponse(
            success=False,
            data={},
            error=result.get("error", "Order lookup failed"),
        )
    data = result.get("data") or {}
    orders = data.get("orders", []) if isinstance(data, dict) else []
    if not orders:
        return ToolResponse(success=True, data={"no_orders": True})
    latest = orders[0]
    return ToolResponse(success=True, data={
        "order_id": latest.get("name") or latest.get("id", ""),
        "order_gid": latest.get("id", ""),
    })


async def add_order_tags(*, order_gid: str, tags: List[str]) -> ToolResponse:
    """Add tags to an order (e.g. Positive Feedback)."""
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


__all__ = ["get_customer_latest_order", "add_order_tags"]
