"""Shared low-level HTTP helper for all hackathon tool endpoints."""

from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from schemas.internal import ToolResponse

API_URL = os.environ.get("API_URL", "").rstrip("/")


async def post_tool(path: str, payload: Dict[str, Any]) -> ToolResponse:
    """POST to a hackathon tool endpoint and normalise the response."""

    if not API_URL:
        return ToolResponse(success=False, error="API_URL is not configured.")

    url = "%s/%s" % (API_URL, path.lstrip("/"))

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
    except Exception as exc:
        return ToolResponse(success=False, error="HTTP error: %s" % exc)

    if resp.status_code != 200:
        return ToolResponse(success=False, error="Non-200 from %s: %s" % (url, resp.status_code))

    try:
        body = resp.json()
    except Exception as exc:
        return ToolResponse(success=False, error="Invalid JSON: %s" % exc)

    if not isinstance(body, dict):
        return ToolResponse(success=False, error="Unexpected response shape")

    success = bool(body.get("success"))
    data = body.get("data") or {}
    error = body.get("error")
    if not success and not error:
        error = "Tool call failed without error message."
    if not isinstance(data, dict):
        data = {}

    return ToolResponse(success=success, data=data, error=error)
