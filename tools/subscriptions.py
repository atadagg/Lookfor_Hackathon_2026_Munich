"""Subscription platform tool adapters."""

from __future__ import annotations

from datetime import datetime, timedelta

from schemas.internal import ToolResponse
from .api import API_URL, post_tool


# ── Tool executors ─────────────────────────────────────────────────


async def subscription_get_details(*, shopifyCustomerId: str) -> dict:
    if API_URL:
        resp = await post_tool("subscription_get_details", {"shopifyCustomerId": shopifyCustomerId})
        return resp.model_dump()
    return {"success": True, "data": {
        "subscription_id": "sub-2001",
        "status": "active",
        "product": "BuzzPatch Monthly (60-pack)",
        "interval": "monthly",
        "next_order_date": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "price": "24.99",
    }, "error": None}


async def subscription_skip_next(*, subscriptionId: str, months: int = 1) -> dict:
    if API_URL:
        resp = await post_tool("subscription_skip_next", {"subscriptionId": subscriptionId, "months": months})
        return resp.model_dump()
    return {"success": True, "data": {
        "subscription_id": subscriptionId,
        "skipped_months": months,
        "next_order_date": (datetime.utcnow() + timedelta(days=30 * (months + 1))).strftime("%Y-%m-%d"),
    }, "error": None}


async def subscription_apply_discount(*, subscriptionId: str, discountPercent: int, numberOfOrders: int) -> dict:
    if API_URL:
        resp = await post_tool("subscription_apply_discount", {
            "subscriptionId": subscriptionId,
            "discountPercent": discountPercent,
            "numberOfOrders": numberOfOrders,
        })
        return resp.model_dump()
    return {"success": True, "data": {
        "subscription_id": subscriptionId,
        "discount_percent": discountPercent,
        "applies_to_next_n_orders": numberOfOrders,
    }, "error": None}


async def subscription_cancel(*, subscriptionId: str, reason: str = "") -> dict:
    if API_URL:
        resp = await post_tool("subscription_cancel", {"subscriptionId": subscriptionId, "reason": reason})
        return resp.model_dump()
    return {"success": True, "data": {
        "subscription_id": subscriptionId,
        "status": "cancelled",
    }, "error": None}


async def subscription_swap_product(*, subscriptionId: str, newProductId: str) -> dict:
    if API_URL:
        resp = await post_tool("subscription_swap_product", {
            "subscriptionId": subscriptionId, "newProductId": newProductId,
        })
        return resp.model_dump()
    return {"success": True, "data": {
        "subscription_id": subscriptionId,
        "new_product": newProductId,
        "swapped": True,
    }, "error": None}


# ── OpenAI function schemas ───────────────────────────────────────

SCHEMA_GET_DETAILS = {
    "type": "function",
    "function": {
        "name": "subscription_get_details",
        "description": "Look up a customer's subscription status, product, and next order date.",
        "parameters": {
            "type": "object",
            "properties": {
                "shopifyCustomerId": {"type": "string", "description": "Shopify customer ID"},
            },
            "required": ["shopifyCustomerId"],
        },
    },
}

SCHEMA_SKIP_NEXT = {
    "type": "function",
    "function": {
        "name": "subscription_skip_next",
        "description": "Skip the next subscription order for a given number of months.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriptionId": {"type": "string", "description": "Subscription ID"},
                "months": {"type": "integer", "description": "Number of months to skip", "default": 1},
            },
            "required": ["subscriptionId"],
        },
    },
}

SCHEMA_APPLY_DISCOUNT = {
    "type": "function",
    "function": {
        "name": "subscription_apply_discount",
        "description": "Apply a percentage discount to upcoming subscription orders.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriptionId": {"type": "string", "description": "Subscription ID"},
                "discountPercent": {"type": "integer", "description": "Discount percentage (e.g. 20 for 20%)"},
                "numberOfOrders": {"type": "integer", "description": "Number of orders the discount applies to"},
            },
            "required": ["subscriptionId", "discountPercent", "numberOfOrders"],
        },
    },
}

SCHEMA_CANCEL = {
    "type": "function",
    "function": {
        "name": "subscription_cancel",
        "description": "Cancel a subscription. Only use after exhausting retention offers (skip, discount).",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriptionId": {"type": "string", "description": "Subscription ID"},
                "reason": {"type": "string", "description": "Reason for cancellation"},
            },
            "required": ["subscriptionId"],
        },
    },
}

SCHEMA_SWAP_PRODUCT = {
    "type": "function",
    "function": {
        "name": "subscription_swap_product",
        "description": "Swap the product in a subscription to a different one.",
        "parameters": {
            "type": "object",
            "properties": {
                "subscriptionId": {"type": "string", "description": "Subscription ID"},
                "newProductId": {"type": "string", "description": "ID of the new product"},
            },
            "required": ["subscriptionId", "newProductId"],
        },
    },
}

EXECUTORS = {
    "subscription_get_details": subscription_get_details,
    "subscription_skip_next": subscription_skip_next,
    "subscription_apply_discount": subscription_apply_discount,
    "subscription_cancel": subscription_cancel,
    "subscription_swap_product": subscription_swap_product,
}
