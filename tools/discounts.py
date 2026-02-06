"""Discount code tool adapter."""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta

from schemas.internal import ToolResponse
from .api import API_URL, post_tool


async def discount_create_code(
    *, shopifyCustomerId: str, discountPercent: int = 10, lifespanHours: int = 48,
) -> dict:
    if API_URL:
        resp = await post_tool("discount_create_code", {
            "shopifyCustomerId": shopifyCustomerId,
            "discountPercent": discountPercent,
            "lifespanHours": lifespanHours,
        })
        return resp.model_dump()

    code = "SAVE%d-%s" % (
        discountPercent,
        "".join(random.choices(string.ascii_uppercase + string.digits, k=6)),
    )
    expires = (datetime.utcnow() + timedelta(hours=lifespanHours)).isoformat()
    return {"success": True, "data": {
        "code": code,
        "discount_percent": discountPercent,
        "expires_at": expires,
        "single_use": True,
    }, "error": None}


SCHEMA_CREATE_CODE = {
    "type": "function",
    "function": {
        "name": "discount_create_code",
        "description": "Create a one-time discount code for a specific customer. Default is 10%% off with 48-hour lifespan.",
        "parameters": {
            "type": "object",
            "properties": {
                "shopifyCustomerId": {"type": "string", "description": "Shopify customer ID"},
                "discountPercent": {"type": "integer", "description": "Discount percentage", "default": 10},
                "lifespanHours": {"type": "integer", "description": "Hours until code expires", "default": 48},
            },
            "required": ["shopifyCustomerId"],
        },
    },
}

EXECUTORS = {
    "discount_create_code": discount_create_code,
}
