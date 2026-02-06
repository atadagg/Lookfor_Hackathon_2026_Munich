# Refund Request (UC4) — Test Roadmap

This document specifies the **MUST-HAVE behavior** for the Refund Request use case.

---

## Workflow (from hackathon manual)

### Step 1 – Check the customer's order
- [ ] **1.1** Look up customer's orders (shopify_get_customer_orders by email).
- [ ] **1.2** Get order details and status.

### Step 2 – Ask for the reason
- [ ] **2.1** Determine refund reason: expectations / shipping delay / damaged-wrong / changed mind.

### Step 3 – Route by reason

#### Route A: Product didn't meet expectations
- [ ] **3A.1** Ask follow-up to identify cause.
- [ ] **3A.2** Share correct usage tip.
- [ ] **3A.3** Offer product swap.
- [ ] **3A.4** If still wants refund: offer store credit with 10% bonus first.
- [ ] **3A.5** If declined: cash refund (ORIGINAL_PAYMENT_METHODS).
- [ ] **3A.6** Tag appropriately.

#### Route B: Shipping delay
- [ ] **3B.1** Check day of week (Mon-Tue: wait until Friday; Wed-Sun: wait until next week).
- [ ] **3B.2** If refuse to wait: offer free replacement → escalate to Monica.

#### Route C: Damaged or wrong item
- [ ] **3C.1** Offer free replacement OR store credit.
- [ ] **3C.2** If replacement: escalate to support.
- [ ] **3C.3** If store credit: issue with bonus.

#### Route D: Changed mind
- [ ] **3D.1** If unfulfilled: cancel order (shopify_cancel_order) and tag.
- [ ] **3D.2** If fulfilled: offer store credit with bonus, then cash refund if declined.

### Step 4 – Execute and close
- [ ] **4.1** Store credit: confirm amount and availability at checkout.
- [ ] **4.2** Cash refund: confirm amount and processing time.
- [ ] **4.3** Cancel: confirm cancellation and refund.

---

## Example intents (must route to refund)

- "I'd like a refund. The patches didn't work for my child."
- "Please refund order #51234; product arrived too late."
- "Want my money back—stickers don't repel mosquitoes as promised."
- "I want to cancel. I changed my mind."

---

## Tool usage (required)

| Tool | When |
|------|------|
| `get_customer_latest_order` | Step 1 – order lookup |
| `cancel_order` | Route D – changed mind (unfulfilled) |
| `refund_order_cash` | Routes A, D – cash refund |
| `create_store_credit` | Routes A, C, D – store credit |
| `add_order_tags` | All routes – tag outcomes |

---

## Test suite layout

| File | Purpose |
|------|---------|
| `test_refund_01_basic_workflow.py` | Routes A-D, store credit first, tags |
| `test_refund_02_edge_cases.py` | Missing data, malformed input, unicode |
| `test_refund_03_tool_failures.py` | Tool errors → graceful handling |
| `test_refund_04_escalation_scenarios.py` | Shipping delay replacement → Monica |
| `test_refund_05_multiturn_complexity.py` | Memory, multi-route conversations |
| `test_refund_09_integration_real_llm.py` | Real LLM routing and execution |

---

## Definition of done

- All tests in `tests/refund/` pass.
- Router sends "refund request" intents to `refund` agent.
- Agent routes correctly by reason (expectations / shipping / damaged / changed mind).
- Store credit offered first (10% bonus), then cash refund.
- Proper escalation for shipping delays and replacements.
- Correct tags applied for each outcome.
