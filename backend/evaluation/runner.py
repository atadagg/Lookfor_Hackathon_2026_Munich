"""Run tickets through the /chat API and collect RunResults."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from .models import RunResult, Ticket


async def run_single_ticket_async(
    ticket: Ticket,
    base_url: str,
    client: httpx.AsyncClient,
    *,
    timeout: float = 60.0,
) -> RunResult:
    """Send all turns of one ticket to POST /chat and return the last turn's result."""
    result = RunResult(ticket=ticket)
    last_response: Optional[Dict[str, Any]] = None

    for turn_idx, (message_text,) in enumerate(ticket.iter_messages()):
        if not message_text.strip():
            continue
        payload = ticket.to_chat_payload(message_text)
        result.turns += 1
        start = time.perf_counter()
        try:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat",
                json=payload,
                timeout=timeout,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            if result.latency_ms is None:
                result.latency_ms = 0.0
            result.latency_ms += latency_ms

            if resp.status_code != 200:
                result.error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                last_response = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                break
            last_response = resp.json()
        except Exception as e:
            result.error = str(e)
            break

    if last_response:
        st = last_response.get("state") or {}
        result.agent = last_response.get("agent") or st.get("routed_agent") or ""
        result.intent = st.get("intent") or ""
        result.is_escalated = st.get("is_escalated", False)
        result.last_assistant_message = st.get("last_assistant_message")
        result.state = st
    return result


def run_single_ticket_sync(
    ticket: Ticket,
    base_url: str,
    *,
    timeout: float = 60.0,
) -> RunResult:
    """Synchronous version: run one ticket with a new client."""
    payloads: List[Dict[str, Any]] = []
    for (msg,) in ticket.iter_messages():
        if msg.strip():
            payloads.append(ticket.to_chat_payload(msg))
    if not payloads:
        return RunResult(ticket=ticket, error="no messages")

    result = RunResult(ticket=ticket)
    last_response = None
    with httpx.Client(timeout=timeout) as client:
        for payload in payloads:
            result.turns += 1
            start = time.perf_counter()
            try:
                resp = client.post(f"{base_url.rstrip('/')}/chat", json=payload)
                latency_ms = (time.perf_counter() - start) * 1000
                if result.latency_ms is None:
                    result.latency_ms = 0.0
                result.latency_ms += latency_ms
                if resp.status_code != 200:
                    result.error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                    last_response = resp.json() if "application/json" in (resp.headers.get("content-type") or "") else {}
                    break
                last_response = resp.json()
            except Exception as e:
                result.error = str(e)
                break

    if last_response:
        st = last_response.get("state") or {}
        result.agent = last_response.get("agent") or st.get("routed_agent") or ""
        result.intent = st.get("intent") or ""
        result.is_escalated = st.get("is_escalated", False)
        result.last_assistant_message = st.get("last_assistant_message")
        result.state = st
    return result


def run_tickets_sync(
    tickets: List[Ticket],
    base_url: str,
    *,
    timeout: float = 60.0,
) -> List[RunResult]:
    """Run all tickets synchronously (one-by-one). Use when not in an async context."""
    return [run_single_ticket_sync(t, base_url, timeout=timeout) for t in tickets]


async def run_tickets(
    tickets: List[Ticket],
    base_url: str,
    *,
    timeout: float = 60.0,
    concurrency: int = 1,
) -> List[RunResult]:
    """Run all tickets against the chat API. If concurrency > 1, runs in parallel (async)."""
    import asyncio
    if concurrency <= 1:
        results: List[RunResult] = []
        async with httpx.AsyncClient(timeout=timeout) as client:
            for t in tickets:
                r = await run_single_ticket_async(t, base_url, client, timeout=timeout)
                results.append(r)
        return results
    results = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        sem = asyncio.Semaphore(concurrency)

        async def run_one(t: Ticket) -> RunResult:
            async with sem:
                return await run_single_ticket_async(t, base_url, client, timeout=timeout)

        results = await asyncio.gather(*[run_one(t) for t in tickets])
    return list(results)
