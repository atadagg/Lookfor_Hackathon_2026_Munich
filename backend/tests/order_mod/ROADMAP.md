# Order Modification (UC5) — Test Roadmap

This document specifies the **MUST-HAVE behavior** for Order Modification (cancel + address update).

---

## Workflow (from hackathon manual)

### Order Cancellation

#### Step 1 – Check the customer's orders
- [ ] **1.1** Look up customer's orders by email.
- [ ] **1.2** Get order status (must be UNFULFILLED to cancel).

#### Step 2 – Ask for the reason
- [ ] **2.1** Determine cancellation reason: shipping delay / accidental order / changed mind.

#### Step 3 – Route by reason

**A) Shipping delay:**
- [ ] **3A.1** Mon-Tue: ask to wait until Friday.
- [ ] **3A.2** Wed-Sun: ask to wait until early next week.
- [ ] **3A.3** If they insist: cancel the order.

**B) Accidental order:**
- [ ] **3B.1** Cancel immediately (shopify_cancel_order, reason=CUSTOMER).
- [ ] **3B.2** Tag: "Accidental Order – Cancelled".

**C) Changed mind:**
- [ ] **3C.1** Cancel (shopify_cancel_order, reason=CUSTOMER).
- [ ] **3C.2** Tag appropriately.

### Update Shipping Address

#### Step 1 – Validation
- [ ] **1.1** Check order was placed TODAY (same date).
- [ ] **1.2** Check order status is UNFULFILLED.

#### Step 2 – Execute or escalate
- [ ] **2.1** If BOTH true: update address (shopify_update_order_shipping_address).
- [ ] **2.2** Tag: "customer verified address".
- [ ] **2.3** If EITHER fails: escalate to Monica.

---

## Example intents (must route to order_mod)

- "I need to cancel my order. I placed it by accident."
- "Accidentally ordered twice—please cancel one."
- "Can I update my shipping address? I entered the wrong one."
- "Cancel order #67890 before it ships, thanks."

---

## Tool usage (required)

| Tool | When |
|------|------|
| `get_customer_latest_order` | Step 1 – order lookup + status |
| `cancel_order` | Cancellation flows |
| `update_shipping_address` | Address update flow |
| `add_order_tags` | Tag all modifications |

---

## Definition of done

- All tests in `tests/order_mod/` pass.
- Router sends "cancel" / "address update" intents to `order_mod` agent.
- Cancel only works for UNFULFILLED orders.
- Address update only works for UNFULFILLED + placed TODAY.
- Proper escalation when conditions not met.
- Correct tags applied.
