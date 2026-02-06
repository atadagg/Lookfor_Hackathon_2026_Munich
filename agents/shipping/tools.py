"""Mock tools for the Shipping (WISMO) specialist.

These are **Python adapters** that simulate the external Shopify tools
used during development. In production you would replace their internals
with real HTTP calls, but the return type must always be `ToolResponse`.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from schemas.internal import ToolResponse


async def get_order_status(shopify_customer_id: str) -> ToolResponse:
    """Mock: fetch the latest order status for a Shopify customer.

    In a real implementation this would call the hackathon endpoint
    `shopify_get_customer_orders` and then potentially
    `shopify_get_order_details`. For this vertical slice we simply return
    a hard-coded "IN_TRANSIT" status with a synthetic tracking URL.
    """

    # TODO: replace with real API integration.
    mocked_order: Dict[str, Any] = {
        "order_id": "#1001",
        "status": "IN_TRANSIT",  # UNFULFILLED | IN_TRANSIT | DELIVERED | CANCELLED
        "created_at": datetime.utcnow().isoformat(),
        "tracking_url": "https://tracking.example.com/demo123",
    }

    return ToolResponse(success=True, data=mocked_order)


async def get_tracking_link(order_id: str) -> ToolResponse:
    """Mock: return a tracking link for the given order id.

    In reality this would likely be redundant with `get_order_status`,
    but keeping it separate mirrors the idea of focused tools.
    """

    # TODO: replace with real tracking URL lookup.
    return ToolResponse(
        success=True,
        data={
            "order_id": order_id,
            "tracking_url": f"https://tracking.example.com/{order_id.lstrip('#')}",
        },
    )


__all__ = ["get_order_status", "get_tracking_link"]
