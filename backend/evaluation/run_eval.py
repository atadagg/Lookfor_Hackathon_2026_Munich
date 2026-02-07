#!/usr/bin/env python3
"""CLI to run the evaluation pipeline: load tickets → run against /chat → metrics → HTML report.

Usage:
  # From repo root (backend as cwd or PYTHONPATH includes backend):
  python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --base-url http://localhost:8000 --out-dir ./eval_out

  # From backend/:
  python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --base-url http://localhost:8000 --out-dir ./eval_out

  # Load from API instead of file:
  python -m evaluation.run_eval --tickets-api-url https://api.example.com/tickets --base-url http://localhost:8000 --out-dir ./eval_out

  # Limit number of tickets (e.g. for a quick smoke test):
  python -m evaluation.run_eval --tickets sample.jsonl --base-url http://localhost:8000 --limit 50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure backend is on path when run as script
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND = _SCRIPT_DIR.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from evaluation.loader import load_tickets_from_file, load_tickets_from_api
from evaluation.runner import run_tickets_sync
from evaluation.metrics import compute_summary
from evaluation.report import write_html_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run evaluation: load tickets, call /chat, write metrics and HTML report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--tickets",
        type=str,
        help="Path to JSON/JSONL file with tickets (each object: conversation_id, user_id, message, optional expected_agent, expected_intent).",
    )
    parser.add_argument(
        "--tickets-api-url",
        type=str,
        help="URL to fetch tickets from (GET; expects JSON with 'tickets' array or array root). Pagination: ?page=1&limit=500.",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the chat API (default: http://localhost:8000).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="./eval_out",
        help="Output directory for report and results JSON (default: ./eval_out).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of tickets to run (0 = no limit).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Request timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing HTML report; only write results JSON.",
    )
    args = parser.parse_args()

    if not args.tickets and not args.tickets_api_url:
        parser.error("Provide either --tickets <file> or --tickets-api-url <url>")

    # Load tickets
    if args.tickets:
        try:
            tickets = load_tickets_from_file(args.tickets)
        except FileNotFoundError:
            # Try relative to backend
            backend_tickets = Path(_BACKEND) / args.tickets
            if backend_tickets.exists():
                tickets = load_tickets_from_file(backend_tickets)
            else:
                print(f"Error: tickets file not found: {args.tickets}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Error loading tickets: {e}", file=sys.stderr)
            return 1
    else:
        try:
            tickets = load_tickets_from_api(args.tickets_api_url, limit=args.limit or 10_000)
        except Exception as e:
            print(f"Error fetching tickets from API: {e}", file=sys.stderr)
            return 1

    if args.limit and args.limit > 0:
        tickets = tickets[: args.limit]
    if not tickets:
        print("No tickets to run.", file=sys.stderr)
        return 0

    print(f"Running {len(tickets)} tickets against {args.base_url} ...")
    results = run_tickets_sync(tickets, args.base_url, timeout=args.timeout)
    summary = compute_summary(results)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results JSON (minimal: summary + result list with key fields)
    results_data = [
        {
            "conversation_id": r.ticket.conversation_id,
            "agent": r.agent,
            "intent": r.intent,
            "is_escalated": r.is_escalated,
            "error": r.error,
            "routing_correct": r.routing_correct,
            "expected_agent": r.ticket.expected_agent,
            "latency_ms": r.latency_ms,
        }
        for r in results
    ]
    results_path = out_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": summary.total,
                "escalated": summary.escalated,
                "errors": summary.errors,
                "routing_accuracy": summary.routing_accuracy,
                "escalation_rate": summary.escalation_rate,
                "results": results_data,
            },
            f,
            indent=2,
        )
    print(f"Wrote {results_path}")

    if not args.no_report:
        report_path = out_dir / "report.html"
        write_html_report(summary, report_path)
        print(f"Wrote {report_path}")

    # Print short summary to stdout
    print(f"\n--- Summary ---")
    print(f"Total: {summary.total} | Auto-handled: {summary.total - summary.escalated - summary.errors} | Escalated: {summary.escalated} | Errors: {summary.errors}")
    print(f"Escalation rate: {100.0 * summary.escalation_rate:.1f}%")
    if summary.routing_accuracy is not None:
        print(f"Routing accuracy: {100.0 * summary.routing_accuracy:.1f}% (n={summary.routing_total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
