# Product Issue (No Effect) Test Suite

TDD test suite for the **Product Issue – "No Effect"** graph-based workflow.

**All tests are written to FAIL against the current `ConversationalAgent`
implementation.** They define the contract that the LangGraph-based
workflow must satisfy. Tests will pass only once `graph.py` is implemented.

## Why Tests Fail Today

The current `ProductIssueAgent` is a `ConversationalAgent` (LLM-driven).
It does NOT:
- Set `workflow_step` to specific values (e.g. `awaiting_goal`)
- Call tools deterministically from graph nodes (e.g. `shopify_get_customer_orders`)
- Store order data in `internal_data` (e.g. `order_id`, `order_gid`)
- Escalate deterministically for missing email
- Progress through multi-turn steps (goal → usage → route → credit/refund)

## Workflow Specification

**Expected graph steps:**

| Step | workflow_step | What happens |
|------|--------------|--------------|
| 1 | `awaiting_goal` | Check order + ask customer's goal |
| 2 | `awaiting_usage` | Ask usage (how many, what time, how many nights) |
| 3a | `routed_usage_fix` | Usage wrong → share correct usage, try 3 nights |
| 3b | `routed_product_swap` | Product mismatch → offer better fit |
| 4 | `offered_store_credit` | Still disappointed → 10% bonus store credit |
| 5a | `recovered` | Accepted → credit issued, tag "No Effect – Recovered" |
| 5b | `cash_refunded` | Declined → cash refund, tag "No Effect – Cash Refund" |
| E1 | `escalated_missing_email` | No email → escalate |
| E2 | `escalated_tool_error` | Tool failure → escalate |

## Test Files

| File | Description | Tests |
|------|-------------|-------|
| `test_product_issue_01_basic_workflow.py` | First turn: check order, set awaiting_goal, tool traces | 8 |
| `test_product_issue_02_edge_cases.py` | Missing email escalates, missing names work, unicode | 8 |
| `test_product_issue_03_tool_failures.py` | Patched tool failures → escalation, traces recorded | 6 |
| `test_product_issue_04_escalation_scenarios.py` | Escalation paths, summaries, thread blocking | 5 |
| `test_product_issue_05_multiturn_complexity.py` | Full flow: goal → usage → route → credit/refund + tags | 10 |

**Total: 37 tests** (all async, all require graph implementation to pass)

## Running Tests

```bash
# All product_issue tests:
pytest backend/tests/product_issue/ -v --tb=short

# Expect: 37 FAILED (until graph.py is implemented)
```

## Tags (applied via shopify_add_tags)

- `"No Effect – Recovered"` — customer accepted store credit
- `"No Effect – Cash Refund"` — customer chose cash refund to original payment

## Refund method

Cash refunds use `refundMethod: "ORIGINAL_PAYMENT_METHODS"`.
