"""Order Modification agent composite tools.

Wraps Shopify tools for order lookup, cancellation, and address update.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from schemas.internal import ToolResponse
from tools.shopify import (
    shopify_add_tags,
    shopify_cancel_order,
    shopify_get_customer_orders,
    shopify_get_order_details,
    shopify_update_order_shipping_address,
)


async def get_customer_latest_order(*, email: str) -> ToolResponse:
    """Get the latest order for a customer by email (with details)."""
    orders_result = await shopify_get_customer_orders(email=email, after="null", limit=10)
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
    return ToolResponse(success=True, data={
        "order_id": d.get("name") or order_name,
        "order_gid": d.get("id", ""),
        "status": (d.get("status") or "").upper(),
        "created_at": d.get("createdAt", ""),
    })


async def cancel_order(
    *,
    order_gid: str,
    reason: str = "CUSTOMER",
    staff_note: str = "",
) -> ToolResponse:
    """Cancel an order."""
    result = await shopify_cancel_order(
        orderId=order_gid,
        reason=reason,
        notifyCustomer=True,
        restock=True,
        staffNote=staff_note,
        refundMode="ORIGINAL",
        storeCredit={"expiresAt": None},
    )
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Cancel order failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


async def update_shipping_address(
    *,
    order_gid: str,
    new_address: Dict[str, Any],
) -> ToolResponse:
    """Update shipping address for an order."""
    result = await shopify_update_order_shipping_address(
        orderId=order_gid,
        newShippingAddress=new_address,
    )
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Update address failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


async def add_order_tags(*, order_gid: str, tags: list) -> ToolResponse:
    """Add tags to an order."""
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


__all__ = [
    "get_customer_latest_order",
    "cancel_order",
    "update_shipping_address",
    "add_order_tags",
]
