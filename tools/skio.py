"""Skio subscription tool adapters — all 5 tools from the hackathon spec.

Endpoints: {API_URL}/hackhaton/...  (note: "hackhaton" is the spec spelling)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from schemas.internal import ToolResponse
from .api import API_URL, post_tool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# 14) skio_cancel_subscription
# =====================================================================

async def skio_cancel_subscription(
    *, subscriptionId: str, cancellationReasons: list,
) -> dict:
    payload = {"subscriptionId": subscriptionId, "cancellationReasons": cancellationReasons}
    if API_URL:
        resp = await post_tool("hackhaton/cancel-subscription", payload)
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_CANCEL_SUBSCRIPTION = {
    "type": "function",
    "function": {
        "name": "skio_cancel_subscription",
        "description": "Cancel a subscription.",
        "parameters": {
            "type": "object",
            "required": ["subscriptionId", "cancellationReasons"],
            "properties": {
                "subscriptionId": {"type": "string", "description": "ID of the subscription to cancel."},
                "cancellationReasons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Reasons for cancellation.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 15) skio_get_subscription_status
# =====================================================================

async def skio_get_subscription_status(*, email: str) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/get-subscription-status", {"email": email})
        return resp.model_dump()
    # Mock
    next_billing = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")
    return {
        "success": True,
        "data": {
            "status": "ACTIVE",
            "subscriptionId": "sub_mock_123",
            "nextBillingDate": next_billing,
        },
        "error": None,
    }


SCHEMA_GET_SUBSCRIPTION_STATUS = {
    "type": "function",
    "function": {
        "name": "skio_get_subscription_status",
        "description": "Get the subscription status of a customer by email.",
        "parameters": {
            "type": "object",
            "required": ["email"],
            "properties": {
                "email": {"type": "string", "description": "Customer email."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 16) skio_pause_subscription
# =====================================================================

async def skio_pause_subscription(
    *, subscriptionId: str, pausedUntil: str,
) -> dict:
    payload = {"subscriptionId": subscriptionId, "pausedUntil": pausedUntil}
    if API_URL:
        resp = await post_tool("hackhaton/pause-subscription", payload)
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_PAUSE_SUBSCRIPTION = {
    "type": "function",
    "function": {
        "name": "skio_pause_subscription",
        "description": "Pause a subscription until a specific date.",
        "parameters": {
            "type": "object",
            "required": ["subscriptionId", "pausedUntil"],
            "properties": {
                "subscriptionId": {"type": "string", "description": "ID of the subscription to pause."},
                "pausedUntil": {"type": "string", "description": "Date to pause until (YYYY-MM-DD)."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 17) skio_skip_next_order_subscription
# =====================================================================

async def skio_skip_next_order_subscription(*, subscriptionId: str) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/skip-next-order-subscription", {"subscriptionId": subscriptionId})
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_SKIP_NEXT_ORDER = {
    "type": "function",
    "function": {
        "name": "skio_skip_next_order_subscription",
        "description": "Skip the next order of an ongoing subscription.",
        "parameters": {
            "type": "object",
            "required": ["subscriptionId"],
            "properties": {
                "subscriptionId": {"type": "string", "description": "ID of the subscription."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 18) skio_unpause_subscription
# =====================================================================

async def skio_unpause_subscription(*, subscriptionId: str) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/unpause-subscription", {"subscriptionId": subscriptionId})
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_UNPAUSE_SUBSCRIPTION = {
    "type": "function",
    "function": {
        "name": "skio_unpause_subscription",
        "description": "Unpause a paused subscription.",
        "parameters": {
            "type": "object",
            "required": ["subscriptionId"],
            "properties": {
                "subscriptionId": {"type": "string", "description": "ID of the subscription to unpause."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# EXECUTORS
# =====================================================================

EXECUTORS = {
    "skio_cancel_subscription": skio_cancel_subscription,
    "skio_get_subscription_status": skio_get_subscription_status,
    "skio_pause_subscription": skio_pause_subscription,
    "skio_skip_next_order_subscription": skio_skip_next_order_subscription,
    "skio_unpause_subscription": skio_unpause_subscription,
}
