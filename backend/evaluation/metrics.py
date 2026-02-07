"""Compute aggregate metrics from a list of RunResults."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from .models import EvalSummary, RunResult


def compute_summary(results: List[RunResult]) -> EvalSummary:
    """Aggregate metrics: counts, escalation rate, routing accuracy, by-agent, latency."""
    summary = EvalSummary(results=results)
    if not results:
        return summary

    summary.total = len(results)
    by_agent: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "escalated": 0, "errors": 0})

    for r in results:
        if r.error:
            summary.errors += 1
        if r.is_escalated:
            summary.escalated += 1

        agent = (r.agent or "unknown").strip().lower()
        by_agent[agent]["count"] += 1
        if r.is_escalated:
            by_agent[agent]["escalated"] += 1
        if r.error:
            by_agent[agent]["errors"] += 1

        intent = (r.intent or "unknown").strip()
        summary.by_intent[intent] = summary.by_intent.get(intent, 0) + 1

        if r.routing_correct is not None:
            summary.routing_total += 1
            if r.routing_correct:
                summary.routing_correct += 1
        if r.intent_correct is not None:
            summary.intent_total += 1
            if r.intent_correct:
                summary.intent_correct += 1

        if r.latency_ms is not None:
            summary.latency_ms.append(r.latency_ms)

    summary.by_agent = dict(by_agent)
    return summary
