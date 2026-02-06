# Wrong / Missing Item in Parcel — Test Roadmap

This document is the **MUST-HAVE specification** for the second use case. Tests in this folder are written to satisfy this roadmap; development of the wrong_item agent should be driven by making these tests pass.

---

## Workflow (from hackathon manual)

### Step 1 – Check the customer's order
- [ ] **1.1** Look up customer's orders (e.g. `shopify_get_customer_orders` by email).
- [ ] **1.2** Get order details and what was fulfilled (e.g. `shopify_get_order_details`).
- [ ] **1.3** Use items purchased and fulfilled to understand what’s missing/wrong.

### Step 2 – Ask what happened
- [ ] **2.1** Ask whether it’s **missing item** or **wrong item received** so the right fix is applied.

### Step 3 – Request photos
- [ ] **3.1** Ask for a photo of the items received.
- [ ] **3.2** If there is a packing slip, ask for a photo of that too.
- [ ] **3.3** If possible, ask for a photo of the outside shipping label on the box.
- [ ] **3.4** Tone: “To get this sorted fast, could you send a photo…”

### Step 4 – Offer the fastest resolution first
- [ ] **4.1** **First option:** Offer free reship of the missing item or the correct item.
- [ ] **4.2** If they asked for a refund, explain you can resend immediately and it’s usually faster than a refund.
- [ ] **4.3** If they **do not want reship**, offer **store credit first** (item value + small bonus, e.g. 10%).
  - [ ] **4.3a** If they accept store credit → use `shopify_create_store_credit`, then tag: **“Wrong or Missing, Store Credit Issued”**.
- [ ] **4.4** If they **decline store credit** → refund in cash.
  - [ ] **4.4a** Refund to original payment method (`shopify_refund_order`).
  - [ ] **4.4b** Tag: **“Wrong or Missing, Cash Refund Issued”**.

### Step 5 – Close the loop
- [ ] **5.1** **If reship:** Escalate the ticket to support so they can resend the order. Do **not** auto-resend; escalate.
- [ ] **5.2** **If store credit:** Confirm the credit amount and that it’s available immediately at checkout.
- [ ] **5.3** **If cash refund:** Confirm the amount and expected processing time.

### Step 6 – Tags
- [ ] **6.1** Use `shopify_add_tags` with order GID when:
  - Store credit issued → tag **“Wrong or Missing, Store Credit Issued”**.
  - Cash refund issued → tag **“Wrong or Missing, Cash Refund Issued”**.

### Step 7 – Escalation
- [ ] **7.1** Reship choice **must** trigger escalation (human processes resend).
- [ ] **7.2** Escalation message should mention looping in support/Monica so support can resend.

---

## Example intents (must route to wrong_item)

- “Got Zen stickers instead of Focus—kids need them for school, help!”
- “My package arrived with only 2 of the 3 packs I paid for.”
- “Received the pet collar but the tick stickers are missing.”

---

## Tool usage (required)

| Tool | When |
|------|------|
| `shopify_get_customer_orders` | Step 1 – look up orders by email |
| `shopify_get_order_details` | Step 1 – get order + line items / fulfilled |
| `shopify_get_product_details` | Optional – to clarify product names |
| `shopify_create_store_credit` | Step 4 – when customer accepts store credit |
| `shopify_refund_order` | Step 4 – when customer declines store credit (cash refund) |
| `shopify_add_tags` | Step 6 – after store credit or refund |
| `shopify_create_return` | Optional – if return is part of flow |
| `escalate_to_human` | Step 5 – when customer chooses reship or when cannot proceed |

---

## Test suite layout (aligned with WISMO)

| File | Purpose |
|------|---------|
| `test_wrong_item_01_basic_workflow.py` | Step 1–5: order check, ask what happened, photos, reship/credit/refund, escalation |
| `test_wrong_item_02_edge_cases.py` | Missing data, malformed input, unicode, etc. |
| `test_wrong_item_03_tool_failures.py` | Tool returns success=false or timeout → graceful handling / escalation |
| `test_wrong_item_04_escalation_scenarios.py` | Reship → escalate; store credit/refund → correct tags and confirmations |
| `test_wrong_item_05_multiturn_complexity.py` | Memory, duplicate detection, state across turns |
| `test_wrong_item_09_integration_real_llm.py` | Real LLM: routing, tool use, and responses |

---

## Definition of done

- All tests in `tests/wrong_item/` pass.
- Router sends “wrong item / missing item” intents to `wrong_item` agent.
- Agent follows the order-check → ask what happened → photos → reship (escalate) / store credit / refund flow.
- Reship always escalates; store credit and refund use correct tools and tags.
- ROADMAP checkboxes above are satisfied by implementation.
