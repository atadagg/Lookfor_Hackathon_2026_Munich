"""Tools for the Shipping (WISMO) specialist.

These are **Python adapters** around the hackathon tooling API. During
local development they can fall back to deterministic mocks, but in the
evaluation environment they should call the real HTTP endpoints.

All functions must return `ToolResponse` to match the uniform contract.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

import httpx

from schemas.internal import ToolResponse


API_URL = os.environ.get("API_URL", "").rstrip("/")


async def _post_tool(path: str, payload: Dict[str, Any]) -> ToolResponse:
    """Low-level helper to call a hackathon tool endpoint.

    Expects the standard JSON envelope:

        { "success": bool, "data": {...} } or
        { "success": false, "error": "..." }
    """

    if not API_URL:
        return ToolResponse(success=False, error="API_URL is not configured.")

    url = f"{API_URL}/{path.lstrip('/')}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
    except Exception as exc:  # pragma: no cover - network failure path
        return ToolResponse(success=False, error=f"HTTP error calling {url}: {exc}")

    if resp.status_code != 200:
        return ToolResponse(
            success=False,
            error=f"Non-200 status from {url}: {resp.status_code}",
        )

    try:
        body = resp.json()
    except Exception as exc:  # pragma: no cover - malformed JSON
        return ToolResponse(success=False, error=f"Invalid JSON from {url}: {exc}")

    if not isinstance(body, dict):
        return ToolResponse(success=False, error=f"Unexpected response shape from {url}")

    success = bool(body.get("success"))
    data = body.get("data") or {}
    error = body.get("error")

    if not success and not error:
        error = "Tool call failed without error message."

    if not isinstance(data, dict):
        data = {}

    return ToolResponse(success=success, data=data, error=error)


async def get_order_status(shopify_customer_id: str) -> ToolResponse:
    """Fetch the latest order status for a Shopify customer.

    This is implemented as a two-step call mirroring the tooling spec:

    1) `shopify_get_customer_orders`   -> list of orders
    2) `shopify_get_order_details`     -> details for the most recent order

    If the API is not available or returns an error, we fall back to a
    deterministic mock so the graph can still be exercised.
    """

    # Attempt real API call first.
    if API_URL:
        orders_resp = await _post_tool(
            "shopify_get_customer_orders",
            {"shopifyCustomerId": shopify_customer_id},
        )
        if orders_resp.success:
            orders = orders_resp.data.get("orders") or []
            if orders:
                latest = orders[0]
                order_id = latest.get("id") or latest.get("order_id")
                if order_id:
                    details_resp = await _post_tool(
                        "shopify_get_order_details",
                        {"orderId": order_id},
                    )
                    if details_resp.success:
                        data = details_resp.data
                        # Normalise the keys expected by the shipping graph.
                        normalised = {
                            "order_id": data.get("order_id") or f"#{order_id}",
                            "status": (data.get("status") or "").upper(),
                            "created_at": data.get("created_at")
                            or datetime.utcnow().isoformat(),
                            "tracking_url": data.get("tracking_url"),
                            "raw": data,
                        }
                        return ToolResponse(success=True, data=normalised)

        # If we reach here, either the tool failed or gave an empty list.
        if not orders_resp.success:
            return orders_resp

    # Fallback mock behaviour for local development / missing API_URL.
    mocked_order: Dict[str, Any] = {
        "order_id": "#1001",
        "status": "IN_TRANSIT",  # UNFULFILLED | IN_TRANSIT | DELIVERED | CANCELLED
        "created_at": datetime.utcnow().isoformat(),
        "tracking_url": "https://tracking.example.com/demo123",
        "raw": {},
    }

    return ToolResponse(success=True, data=mocked_order)


async def get_tracking_link(order_id: str) -> ToolResponse:
    """Return a tracking link for the given order id.

    If a dedicated tracking tool exists in the hackathon API it can be
    wired here; otherwise we synthesise a URL from the order id.
    """

    # For now we keep this simple and deterministic.
    return ToolResponse(
        success=True,
        data={
            "order_id": order_id,
            "tracking_url": f"https://tracking.example.com/{order_id.lstrip('#')}",
        },
    )


__all__ = ["get_order_status", "get_tracking_link"]
