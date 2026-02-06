"""Discount agent composite tools.

Thin wrapper over shopify_create_discount_code.
"""

from __future__ import annotations

from typing import Optional

from schemas.internal import ToolResponse
from tools.shopify import shopify_create_discount_code


async def create_discount_10_percent(*, duration_hours: int = 48) -> ToolResponse:
    """Create a 10% order-wide discount code valid for specified hours."""
    result = await shopify_create_discount_code(
        type="percentage",
        value=0.1,
        duration=duration_hours,
        productIds=[],
    )
    if result.get("success") is False:
        return ToolResponse(
            success=False,
            data=result.get("data") or {},
            error=result.get("error", "Failed to create discount code"),
        )
    return ToolResponse(success=True, data=result.get("data") or {})


__all__ = ["create_discount_10_percent"]
