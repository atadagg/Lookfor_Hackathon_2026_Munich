# Data evaluation system

Run batches of support “tickets” through the `/chat` API and measure success, escalation rate, routing accuracy, and latency. Outputs JSON results and an HTML report with charts.

## Real tickets API vs file-based tickets

**The Hackathon Tooling Spec you have is for backend *tools* (Shopify/Skio)** — e.g. `shopify_get_customer_orders`, `skio_cancel_subscription`. That spec does **not** define a “tickets API” that serves thousands of support conversations. So we don’t have access to a real tickets API from that spec.

**Until you have a tickets API:**

- Use **file-based tickets**: JSON or JSONL with one ticket per object (or per line). See format below and `tests/evaluation/sample_tickets.jsonl`.
- Run:  
  `python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --base-url http://localhost:8000 --out-dir ./eval_out`

**When you get a tickets API** (e.g. from the hackathon or your own backend):

- The loader supports the **uniform API response** (HTTP 200, JSON):
  - Success: `{ "success": true, "data": [ {...}, ... ] }` or `{ "success": true, "data": { "tickets": [...], "next_page": 2 } }`
  - Failure: `{ "success": false, "error": "..." }` → raises and stops.
- Run:  
  `python -m evaluation.run_eval --tickets-api-url https://... --base-url http://localhost:8000 --out-dir ./eval_out`
- Pagination: if the API returns `next_page`, we request `?page=next_page&limit=500` until no more pages.

## Ticket format (file or API)

Each ticket object must have:

- `conversation_id` (or `id`) – unique thread id
- `message` – single user message, **or** `messages` – array of `{ "role": "user", "content": "..." }` for multi-turn

Optional (for evaluation and reporting):

- `user_id`, `channel`, `customer_email`, `first_name`, `last_name`, `shopify_customer_id`
- `expected_agent` – e.g. `wismo`, `refund` (enables routing accuracy)
- `expected_intent` – e.g. `Shipping Delay – Neutral Status Check` (enables intent accuracy)
- `label` – short name for reports

Example (JSONL, one line per ticket):

```json
{"conversation_id": "eval-1", "user_id": "u1", "message": "Where is my order?", "expected_agent": "wismo"}
{"conversation_id": "eval-2", "user_id": "u2", "message": "I want a refund", "expected_agent": "refund"}
```

## Usage

From the **backend** directory (or with `PYTHONPATH` including backend):

```bash
# File-based (no API)
python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --base-url http://localhost:8000 --out-dir ./eval_out

# With a tickets API (when available)
python -m evaluation.run_eval --tickets-api-url https://api.example.com/tickets --base-url http://localhost:8000 --out-dir ./eval_out

# Limit tickets (e.g. smoke test)
python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --limit 20 --out-dir ./eval_out

# Skip HTML report, only results.json
python -m evaluation.run_eval --tickets tests/evaluation/sample_tickets.jsonl --no-report --out-dir ./eval_out
```

Ensure the chat API is running at `--base-url` before running.

## Output

- `eval_out/results.json` – summary metrics + one object per ticket (agent, intent, is_escalated, routing_correct, latency_ms, etc.).
- `eval_out/report.html` – dashboard with counts, escalation rate, routing accuracy, by-agent breakdown, and sample failures (unless `--no-report`).
