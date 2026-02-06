"""Shopify tool adapters – order management, refunds, credits, tags."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from schemas.internal import ToolResponse
from .api import API_URL, post_tool


# ── Tool executors ─────────────────────────────────────────────────


async def shopify_get_customer_orders(*, shopifyCustomerId: str) -> dict:
    if API_URL:
        resp = await post_tool("shopify_get_customer_orders", {"shopifyCustomerId": shopifyCustomerId})
        return resp.model_dump()
    return {"success": True, "data": {"orders": [
        {"id": "ord-1001", "order_id": "#1001", "status": "fulfilled", "created_at": datetime.utcnow().isoformat()},
    ]}, "error": None}


async def shopify_get_order_details(*, orderId: str) -> dict:
    if API_URL:
        resp = await post_tool("shopify_get_order_details", {"orderId": orderId})
        return resp.model_dump()
    return {"success": True, "data": {
        "order_id": "#%s" % orderId.lstrip("#"),
        "status": "fulfilled",
        "fulfillment_status": "IN_TRANSIT",
        "created_at": datetime.utcnow().isoformat(),
        "tracking_url": "https://tracking.example.com/%s" % orderId.lstrip("#"),
        "items": [
            {"name": "BuzzPatch Mosquito Stickers (60-pack)", "quantity": 1, "price": "29.99"},
            {"name": "ZenPatch Calm Stickers (24-pack)", "quantity": 1, "price": "19.99"},
        ],
        "shipping_address": {"city": "Toronto", "country": "CA"},
    }, "error": None}


async def shopify_cancel_order(*, orderId: str, reason: str = "customer_request") -> dict:
    if API_URL:
        resp = await post_tool("shopify_cancel_order", {"orderId": orderId, "reason": reason})
        return resp.model_dump()
    return {"success": True, "data": {"order_id": orderId, "cancelled": True}, "error": None}


async def shopify_update_shipping_address(*, orderId: str, address: Dict[str, str]) -> dict:
    if API_URL:
        resp = await post_tool("shopify_update_shipping_address", {"orderId": orderId, "address": address})
        return resp.model_dump()
    return {"success": True, "data": {"order_id": orderId, "address_updated": True}, "error": None}


async def shopify_add_order_tags(*, orderId: str, tags: List[str]) -> dict:
    if API_URL:
        resp = await post_tool("shopify_add_order_tags", {"orderId": orderId, "tags": tags})
        return resp.model_dump()
    return {"success": True, "data": {"order_id": orderId, "tags": tags}, "error": None}


async def shopify_create_refund(*, orderId: str, reason: str = "", amount: str = "full") -> dict:
    if API_URL:
        resp = await post_tool("shopify_create_refund", {"orderId": orderId, "reason": reason, "amount": amount})
        return resp.model_dump()
    return {"success": True, "data": {"order_id": orderId, "refund_id": "ref-1001", "status": "processed"}, "error": None}


async def shopify_issue_store_credit(*, shopifyCustomerId: str, amount: str, bonusPercent: int = 0) -> dict:
    if API_URL:
        resp = await post_tool("shopify_issue_store_credit", {
            "shopifyCustomerId": shopifyCustomerId, "amount": amount, "bonusPercent": bonusPercent,
        })
        return resp.model_dump()
    base = float(amount)
    total = base * (1 + bonusPercent / 100)
    return {"success": True, "data": {
        "credit_amount": "%.2f" % total, "bonus_applied": bonusPercent > 0,
    }, "error": None}


# ── OpenAI function schemas ───────────────────────────────────────

SCHEMA_GET_CUSTOMER_ORDERS = {
    "type": "function",
    "function": {
        "name": "shopify_get_customer_orders",
        "description": "Retrieve the list of orders for a Shopify customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "shopifyCustomerId": {"type": "string", "description": "Shopify customer ID"},
            },
            "required": ["shopifyCustomerId"],
        },
    },
}

SCHEMA_GET_ORDER_DETAILS = {
    "type": "function",
    "function": {
        "name": "shopify_get_order_details",
        "description": "Get detailed information about a specific order, including items, status, and tracking.",
        "parameters": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string", "description": "The order ID"},
            },
            "required": ["orderId"],
        },
    },
}

SCHEMA_CANCEL_ORDER = {
    "type": "function",
    "function": {
        "name": "shopify_cancel_order",
        "description": "Cancel a Shopify order. Only use when the workflow explicitly calls for cancellation.",
        "parameters": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string", "description": "The order ID to cancel"},
                "reason": {"type": "string", "description": "Reason for cancellation"},
            },
            "required": ["orderId"],
        },
    },
}

SCHEMA_UPDATE_SHIPPING_ADDRESS = {
    "type": "function",
    "function": {
        "name": "shopify_update_shipping_address",
        "description": "Update the shipping address on an unfulfilled order placed today.",
        "parameters": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string", "description": "The order ID"},
                "address": {"type": "object", "description": "New address object with street, city, state, zip, country"},
            },
            "required": ["orderId", "address"],
        },
    },
}

SCHEMA_ADD_ORDER_TAGS = {
    "type": "function",
    "function": {
        "name": "shopify_add_order_tags",
        "description": "Add tags to an order for logging and tracking actions taken.",
        "parameters": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string", "description": "The order ID"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to add"},
            },
            "required": ["orderId", "tags"],
        },
    },
}

SCHEMA_CREATE_REFUND = {
    "type": "function",
    "function": {
        "name": "shopify_create_refund",
        "description": "Issue a refund for an order to the original payment method.",
        "parameters": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string", "description": "The order ID"},
                "reason": {"type": "string", "description": "Reason for the refund"},
                "amount": {"type": "string", "description": "Amount to refund or 'full'"},
            },
            "required": ["orderId"],
        },
    },
}

SCHEMA_ISSUE_STORE_CREDIT = {
    "type": "function",
    "function": {
        "name": "shopify_issue_store_credit",
        "description": "Issue store credit to a customer's account, optionally with a bonus percentage.",
        "parameters": {
            "type": "object",
            "properties": {
                "shopifyCustomerId": {"type": "string", "description": "Shopify customer ID"},
                "amount": {"type": "string", "description": "Base credit amount"},
                "bonusPercent": {"type": "integer", "description": "Bonus percentage on top (e.g. 10 for 10%)", "default": 0},
            },
            "required": ["shopifyCustomerId", "amount"],
        },
    },
}

# Mapping from function name to executor
EXECUTORS = {
    "shopify_get_customer_orders": shopify_get_customer_orders,
    "shopify_get_order_details": shopify_get_order_details,
    "shopify_cancel_order": shopify_cancel_order,
    "shopify_update_shipping_address": shopify_update_shipping_address,
    "shopify_add_order_tags": shopify_add_order_tags,
    "shopify_create_refund": shopify_create_refund,
    "shopify_issue_store_credit": shopify_issue_store_credit,
}
