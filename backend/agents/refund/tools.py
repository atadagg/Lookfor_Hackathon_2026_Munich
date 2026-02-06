"""Refund agent composite tools.

Wraps Shopify tools for order lookup, cancellation, refunds, store credit, and tagging.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from schemas.internal import ToolResponse
from tools.shopify import (
    shopify_add_tags,
    shopify_cancel_order,
    shopify_create_return,
    shopify_create_store_credit,
    shopify_get_customer_orders,
    shopify_get_order_details,
    shopify_refund_order,
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
        "customer_gid": d.get("customerId") or d.get("customer_id") or "gid://shopify/Customer/200",
        "status": (d.get("status") or "").upper(),
        "created_at": d.get("createdAt", ""),
    })


async def cancel_order(*, order_gid: str, reason: str = "CUSTOMER") -> ToolResponse:
    """Cancel an order."""
    result = await shopify_cancel_order(
        orderId=order_gid,
        reason=reason,
        notifyCustomer=True,
        restock=True,
        staffNote="Customer requested refund",
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


async def create_return(*, order_gid: str) -> ToolResponse:
    """Create a return for an order."""
    result = await shopify_create_return(orderId=order_gid)
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Create return failed"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


async def add_order_tags(*, order_gid: str, tags: List[str]) -> ToolResponse:
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
    "refund_order_cash",
    "create_store_credit",
    "create_return",
    "add_order_tags",
]
