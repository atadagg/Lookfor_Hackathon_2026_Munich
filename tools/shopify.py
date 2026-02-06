"""Shopify tool adapters — all 13 tools from the hackathon tooling spec.

Each tool has:
  - An async executor function (calls the real API or returns a mock)
  - An OpenAI function-calling schema (SCHEMA_*)
  - An entry in the EXECUTORS dict

Endpoints use the exact paths from the spec: {API_URL}/hackhaton/...
(note: "hackhaton" is the spec spelling)
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from schemas.internal import ToolResponse
from .api import API_URL, post_tool


# ── helpers ────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _random_gid(resource: str = "Order") -> str:
    return "gid://shopify/%s/%d" % (resource, random.randint(1000, 999999))


# =====================================================================
# 1) shopify_add_tags
# =====================================================================

async def shopify_add_tags(*, id: str, tags: list) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/add_tags", {"id": id, "tags": tags})
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_ADD_TAGS = {
    "type": "function",
    "function": {
        "name": "shopify_add_tags",
        "description": "Add tags to an order, customer, product, or other Shopify resource.",
        "parameters": {
            "type": "object",
            "required": ["id", "tags"],
            "properties": {
                "id": {"type": "string", "description": "Shopify resource GID."},
                "tags": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                    "description": "Tags to add.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 2) shopify_cancel_order
# =====================================================================

async def shopify_cancel_order(
    *,
    orderId: str,
    reason: str = "CUSTOMER",
    notifyCustomer: bool = True,
    restock: bool = True,
    staffNote: str = "",
    refundMode: str = "ORIGINAL",
    storeCredit: dict = None,
) -> dict:
    payload = {
        "orderId": orderId,
        "reason": reason,
        "notifyCustomer": notifyCustomer,
        "restock": restock,
        "staffNote": staffNote,
        "refundMode": refundMode,
        "storeCredit": storeCredit or {"expiresAt": None},
    }
    if API_URL:
        resp = await post_tool("hackhaton/cancel_order", payload)
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_CANCEL_ORDER = {
    "type": "function",
    "function": {
        "name": "shopify_cancel_order",
        "description": "Cancel an order based on order ID and reason.",
        "parameters": {
            "type": "object",
            "required": ["orderId", "reason", "notifyCustomer", "restock", "staffNote", "refundMode", "storeCredit"],
            "properties": {
                "orderId": {"type": "string", "description": "Order GID."},
                "reason": {
                    "type": "string",
                    "enum": ["CUSTOMER", "DECLINED", "FRAUD", "INVENTORY", "OTHER", "STAFF"],
                    "description": "Cancellation reason.",
                },
                "notifyCustomer": {"type": "boolean", "description": "Notify customer."},
                "restock": {"type": "boolean", "description": "Restock inventory where applicable."},
                "staffNote": {"type": "string", "description": "Internal note (max 255 chars)."},
                "refundMode": {
                    "type": "string",
                    "enum": ["ORIGINAL", "STORE_CREDIT"],
                    "description": "Refund method.",
                },
                "storeCredit": {
                    "type": "object",
                    "description": "Store credit options (only when refundMode=STORE_CREDIT).",
                    "properties": {
                        "expiresAt": {"type": "string", "description": "ISO 8601 timestamp or null for no expiry."},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 3) shopify_create_discount_code
# =====================================================================

async def shopify_create_discount_code(
    *, type: str = "percentage", value: float = 0.1, duration: int = 48, productIds: list = None,
) -> dict:
    payload = {
        "type": type,
        "value": value,
        "duration": duration,
        "productIds": productIds or [],
    }
    if API_URL:
        resp = await post_tool("hackhaton/create_discount_code", payload)
        return resp.model_dump()
    code = "DISCOUNT_LF_%s" % "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return {"success": True, "data": {"code": code}, "error": None}


SCHEMA_CREATE_DISCOUNT_CODE = {
    "type": "function",
    "function": {
        "name": "shopify_create_discount_code",
        "description": "Create a discount code. type='percentage' uses 0-1 values (e.g. 0.1 = 10%), type='fixed' uses absolute amount.",
        "parameters": {
            "type": "object",
            "required": ["type", "value", "duration", "productIds"],
            "properties": {
                "type": {"type": "string", "description": "'percentage' (0-1) or 'fixed' (absolute amount)."},
                "value": {"type": "number", "description": "If percentage, 0-1; if fixed, currency amount."},
                "duration": {"type": "number", "description": "Validity duration in hours (e.g. 48)."},
                "productIds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Product/variant GIDs (empty array for order-wide).",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 4) shopify_create_return
# =====================================================================

async def shopify_create_return(*, orderId: str) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/create_return", {"orderId": orderId})
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_CREATE_RETURN = {
    "type": "function",
    "function": {
        "name": "shopify_create_return",
        "description": "Create a return for an order using Shopify's returnCreate API.",
        "parameters": {
            "type": "object",
            "required": ["orderId"],
            "properties": {
                "orderId": {"type": "string", "description": "Order GID (e.g. 'gid://shopify/Order/...')"},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 5) shopify_create_store_credit
# =====================================================================

async def shopify_create_store_credit(
    *, id: str, creditAmount: dict, expiresAt: str = None,
) -> dict:
    payload = {"id": id, "creditAmount": creditAmount, "expiresAt": expiresAt}
    if API_URL:
        resp = await post_tool("hackhaton/create_store_credit", payload)
        return resp.model_dump()
    amount = creditAmount.get("amount", "10.00")
    currency = creditAmount.get("currencyCode", "USD")
    return {
        "success": True,
        "data": {
            "storeCreditAccountId": _random_gid("StoreCreditAccount"),
            "credited": {"amount": amount, "currencyCode": currency},
            "newBalance": {"amount": str(float(amount) + 50), "currencyCode": currency},
        },
        "error": None,
    }


SCHEMA_CREATE_STORE_CREDIT = {
    "type": "function",
    "function": {
        "name": "shopify_create_store_credit",
        "description": "Issue store credit to a customer.",
        "parameters": {
            "type": "object",
            "required": ["id", "creditAmount", "expiresAt"],
            "properties": {
                "id": {"type": "string", "description": "Customer GID or StoreCreditAccount GID."},
                "creditAmount": {
                    "type": "object",
                    "required": ["amount", "currencyCode"],
                    "properties": {
                        "amount": {"type": "string", "description": "Decimal amount, e.g. '49.99'."},
                        "currencyCode": {"type": "string", "description": "ISO 4217 code, e.g. USD."},
                    },
                    "additionalProperties": False,
                },
                "expiresAt": {"type": "string", "description": "ISO 8601 expiry or null for no expiry."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 6) shopify_get_collection_recommendations
# =====================================================================

async def shopify_get_collection_recommendations(*, queryKeys: list) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/get_collection_recommendations", {"queryKeys": queryKeys})
        return resp.model_dump()
    return {
        "success": True,
        "data": [
            {"id": "gid://shopify/Collection/1", "title": "Best Sellers", "handle": "best-sellers"},
        ],
        "error": None,
    }


SCHEMA_GET_COLLECTION_RECOMMENDATIONS = {
    "type": "function",
    "function": {
        "name": "shopify_get_collection_recommendations",
        "description": "Get collection recommendations based on keyword queries.",
        "parameters": {
            "type": "object",
            "required": ["queryKeys"],
            "properties": {
                "queryKeys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords describing what the customer wants.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 7) shopify_get_customer_orders
# =====================================================================

async def shopify_get_customer_orders(
    *, email: str, after: str = "null", limit: int = 10,
) -> dict:
    payload = {"email": email, "after": after, "limit": limit}
    if API_URL:
        resp = await post_tool("hackhaton/get_customer_orders", payload)
        return resp.model_dump()
    # Mock
    return {
        "success": True,
        "data": {
            "orders": [
                {
                    "id": "gid://shopify/Order/5531567751245",
                    "name": "#1001",
                    "createdAt": _now_iso(),
                    "status": "FULFILLED",
                    "trackingUrl": "https://tracking.example.com/demo123",
                },
            ],
            "hasNextPage": False,
            "endCursor": None,
        },
        "error": None,
    }


SCHEMA_GET_CUSTOMER_ORDERS = {
    "type": "function",
    "function": {
        "name": "shopify_get_customer_orders",
        "description": "Get a customer's orders by email.",
        "parameters": {
            "type": "object",
            "required": ["email", "after", "limit"],
            "properties": {
                "email": {"type": "string", "description": "Customer email."},
                "after": {"type": "string", "description": "Cursor for pagination. Use 'null' for first page."},
                "limit": {"type": "number", "description": "Number of orders to return (max 250)."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 8) shopify_get_order_details
# =====================================================================

async def shopify_get_order_details(*, orderId: str) -> dict:
    # Spec: orderId must start with '#'
    if not orderId.startswith("#"):
        orderId = "#%s" % orderId.lstrip("#")
    if API_URL:
        resp = await post_tool("hackhaton/get_order_details", {"orderId": orderId})
        return resp.model_dump()
    # Mock
    return {
        "success": True,
        "data": {
            "id": "gid://shopify/Order/5531567751245",
            "name": orderId,
            "createdAt": _now_iso(),
            "status": "FULFILLED",
            "trackingUrl": "https://tracking.example.com/%s" % orderId.lstrip("#"),
        },
        "error": None,
    }


SCHEMA_GET_ORDER_DETAILS = {
    "type": "function",
    "function": {
        "name": "shopify_get_order_details",
        "description": "Fetch detailed information for a single order. orderId must start with '#', e.g. '#1234'.",
        "parameters": {
            "type": "object",
            "required": ["orderId"],
            "properties": {
                "orderId": {"type": "string", "description": "Order identifier starting with '#', e.g. '#1234'."},
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 9) shopify_get_product_details
# =====================================================================

async def shopify_get_product_details(*, queryType: str, queryKey: str) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/get_product_details", {
            "queryType": queryType, "queryKey": queryKey,
        })
        return resp.model_dump()
    return {
        "success": True,
        "data": [
            {"id": "gid://shopify/Product/9", "title": "BuzzPatch", "handle": "buzzpatch"},
        ],
        "error": None,
    }


SCHEMA_GET_PRODUCT_DETAILS = {
    "type": "function",
    "function": {
        "name": "shopify_get_product_details",
        "description": "Look up product information by ID, name, or key feature.",
        "parameters": {
            "type": "object",
            "required": ["queryType", "queryKey"],
            "properties": {
                "queryKey": {"type": "string", "description": "Lookup key. If queryType is 'id', must be a Shopify Product GID."},
                "queryType": {
                    "type": "string",
                    "enum": ["id", "name", "key feature"],
                    "description": "How to interpret queryKey.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 10) shopify_get_product_recommendations
# =====================================================================

async def shopify_get_product_recommendations(*, queryKeys: list) -> dict:
    if API_URL:
        resp = await post_tool("hackhaton/get_product_recommendations", {"queryKeys": queryKeys})
        return resp.model_dump()
    return {
        "success": True,
        "data": [
            {"id": "gid://shopify/Product/10", "title": "SleepyPatch", "handle": "sleepypatch"},
            {"id": "gid://shopify/Product/11", "title": "FocusPatch", "handle": "focuspatch"},
        ],
        "error": None,
    }


SCHEMA_GET_PRODUCT_RECOMMENDATIONS = {
    "type": "function",
    "function": {
        "name": "shopify_get_product_recommendations",
        "description": "Get product recommendations based on keyword intents.",
        "parameters": {
            "type": "object",
            "required": ["queryKeys"],
            "properties": {
                "queryKeys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords describing the customer's intent.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 11) shopify_get_related_knowledge_source
# =====================================================================

async def shopify_get_related_knowledge_source(
    *, question: str, specificToProductId: str = None,
) -> dict:
    payload = {"question": question, "specificToProductId": specificToProductId}
    if API_URL:
        resp = await post_tool("hackhaton/get_related_knowledge_source", payload)
        return resp.model_dump()
    return {
        "success": True,
        "data": {"faqs": [], "pdfs": [], "blogArticles": [], "pages": []},
        "error": None,
    }


SCHEMA_GET_RELATED_KNOWLEDGE_SOURCE = {
    "type": "function",
    "function": {
        "name": "shopify_get_related_knowledge_source",
        "description": "Retrieve FAQs, PDFs, blog articles, and pages related to a customer question.",
        "parameters": {
            "type": "object",
            "required": ["question", "specificToProductId"],
            "properties": {
                "question": {"type": "string", "description": "Customer question or problem."},
                "specificToProductId": {
                    "type": "string",
                    "description": "Related product GID, or 'null' if not product-specific.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 12) shopify_refund_order
# =====================================================================

async def shopify_refund_order(*, orderId: str, refundMethod: str) -> dict:
    payload = {"orderId": orderId, "refundMethod": refundMethod}
    if API_URL:
        resp = await post_tool("hackhaton/refund_order", payload)
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_REFUND_ORDER = {
    "type": "function",
    "function": {
        "name": "shopify_refund_order",
        "description": "Refund an order to original payment method or store credit.",
        "parameters": {
            "type": "object",
            "required": ["orderId", "refundMethod"],
            "properties": {
                "orderId": {"type": "string", "description": "Order GID."},
                "refundMethod": {
                    "type": "string",
                    "enum": ["ORIGINAL_PAYMENT_METHODS", "STORE_CREDIT"],
                    "description": "Where the refund goes.",
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# 13) shopify_update_order_shipping_address
# =====================================================================

async def shopify_update_order_shipping_address(
    *, orderId: str, shippingAddress: dict,
) -> dict:
    payload = {"orderId": orderId, "shippingAddress": shippingAddress}
    if API_URL:
        resp = await post_tool("hackhaton/update_order_shipping_address", payload)
        return resp.model_dump()
    return {"success": True, "data": {}, "error": None}


SCHEMA_UPDATE_ORDER_SHIPPING_ADDRESS = {
    "type": "function",
    "function": {
        "name": "shopify_update_order_shipping_address",
        "description": "Update an order's shipping address.",
        "parameters": {
            "type": "object",
            "required": ["orderId", "shippingAddress"],
            "properties": {
                "orderId": {"type": "string", "description": "Order GID."},
                "shippingAddress": {
                    "type": "object",
                    "required": [
                        "firstName", "lastName", "company", "address1",
                        "address2", "city", "provinceCode", "country", "zip", "phone",
                    ],
                    "properties": {
                        "firstName": {"type": "string"},
                        "lastName": {"type": "string"},
                        "company": {"type": "string"},
                        "address1": {"type": "string"},
                        "address2": {"type": "string"},
                        "city": {"type": "string"},
                        "provinceCode": {"type": "string"},
                        "country": {"type": "string"},
                        "zip": {"type": "string"},
                        "phone": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    },
}


# =====================================================================
# EXECUTORS — maps function name → async callable
# =====================================================================

EXECUTORS = {
    "shopify_add_tags": shopify_add_tags,
    "shopify_cancel_order": shopify_cancel_order,
    "shopify_create_discount_code": shopify_create_discount_code,
    "shopify_create_return": shopify_create_return,
    "shopify_create_store_credit": shopify_create_store_credit,
    "shopify_get_collection_recommendations": shopify_get_collection_recommendations,
    "shopify_get_customer_orders": shopify_get_customer_orders,
    "shopify_get_order_details": shopify_get_order_details,
    "shopify_get_product_details": shopify_get_product_details,
    "shopify_get_product_recommendations": shopify_get_product_recommendations,
    "shopify_get_related_knowledge_source": shopify_get_related_knowledge_source,
    "shopify_refund_order": shopify_refund_order,
    "shopify_update_order_shipping_address": shopify_update_order_shipping_address,
}
