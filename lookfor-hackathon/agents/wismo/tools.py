"""WISMO-specific tools (e.g. shipment tracking APIs)."""

from __future__ import annotations

from typing import Any, Dict


async def track_shipment(tracking_number: str) -> Dict[str, Any]:
    """Stub for a tracking API call.

    Replace this with integration to Shopify, AfterShip, or carrier APIs.
    """

    return {
        "tracking_number": tracking_number,
        "status": "in_transit",
        "eta": None,
        "raw": {},
    }


__all__ = ["track_shipment"]
