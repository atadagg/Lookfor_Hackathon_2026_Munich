"""Load evaluation tickets from JSON/JSONL files or from an HTTP API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List

import httpx

from .models import Ticket


def _normalize_ticket(raw: Dict[str, Any]) -> Ticket:
    """Build a Ticket from a dict (file or API)."""
    conv_id = str(raw.get("conversation_id", raw.get("id", "")))
    if not conv_id:
        raise ValueError("ticket must have conversation_id or id")
    user_id = str(raw.get("user_id", "eval-user"))
    message = raw.get("message")
    messages = raw.get("messages")
    if message is None and not messages:
        raise ValueError("ticket must have 'message' or 'messages'")
    return Ticket(
        conversation_id=conv_id,
        user_id=user_id,
        channel=str(raw.get("channel", "email")),
        customer_email=str(raw.get("customer_email", "")),
        first_name=str(raw.get("first_name", "")),
        last_name=str(raw.get("last_name", "")),
        shopify_customer_id=str(raw.get("shopify_customer_id", "")),
        message=message,
        messages=messages,
        expected_agent=raw.get("expected_agent"),
        expected_intent=raw.get("expected_intent"),
        label=raw.get("label"),
    )


def load_tickets_from_file(path: str | Path) -> List[Ticket]:
    """Load tickets from a JSON array file or JSONL (one JSON object per line)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    tickets: List[Ticket] = []

    # Try JSONL first (each line is a JSON object).
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        try:
            first = json.loads(lines[0])
            if isinstance(first, dict) and ("conversation_id" in first or "id" in first):
                for line in lines:
                    obj = json.loads(line)
                    tickets.append(_normalize_ticket(obj))
                return tickets
        except json.JSONDecodeError:
            pass

    # Single JSON array or object.
    data = json.loads(text)
    if isinstance(data, list):
        for item in data:
            tickets.append(_normalize_ticket(item))
    elif isinstance(data, dict):
        if "tickets" in data:
            for item in data["tickets"]:
                tickets.append(_normalize_ticket(item))
        else:
            tickets.append(_normalize_ticket(data))
    else:
        raise ValueError("file must be JSON array, object with 'tickets', or JSONL")
    return tickets


def load_tickets_from_api(
    url: str,
    *,
    limit: int = 10_000,
    page_size: int = 500,
    headers: Dict[str, str] | None = None,
) -> List[Ticket]:
    """Fetch tickets from an HTTP API.

    Supports the hackathon uniform response (HTTP 200, JSON):
    - Success: { "success": true, "data": [ {...}, ... ] } or
      { "success": true, "data": { "tickets": [...], "next_page": 2 } }
    - Failure: { "success": false, "error": "..." } → raises ValueError.

    Also accepts raw JSON: [ {...}, ... ] or { "tickets": [...], "next_page": 2 }.

    Pagination: if response has next_page, next request is url?page=next_page&limit=page_size.
    """
    tickets: List[Ticket] = []
    page = 1
    client = httpx.Client(timeout=60.0, headers=headers or {})

    try:
        while len(tickets) < limit:
            sep = "&" if "?" in url else "?"
            fetch_url = f"{url}{sep}page={page}&limit={page_size}"
            resp = client.get(fetch_url)
            resp.raise_for_status()
            body = resp.json()

            # Hackathon uniform contract: { "success": true, "data": ... } or { "success": false, "error": "..." }
            if isinstance(body, dict) and "success" in body:
                if not body.get("success"):
                    raise ValueError(
                        "Tickets API returned error: " + str(body.get("error", "unknown"))
                    )
                data = body.get("data")
                if data is None:
                    data = body
            else:
                data = body

            if isinstance(data, list):
                batch = data
                next_page = None
            else:
                batch = data.get("tickets", data.get("data", [])) if isinstance(data, dict) else []
                next_page = data.get("next_page") if isinstance(data, dict) else None

            for item in batch:
                if len(tickets) >= limit:
                    break
                tickets.append(_normalize_ticket(item))

            if not batch or next_page is None:
                break
            page = next_page if isinstance(next_page, int) else page + 1
    finally:
        client.close()

    return tickets
