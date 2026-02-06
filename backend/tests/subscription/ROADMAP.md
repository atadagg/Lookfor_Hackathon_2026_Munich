# Subscription Management (UC7) — Test Roadmap

This document specifies the **MUST-HAVE behavior** for Subscription Management.

---

## Workflow (from hackathon manual)

### Step 1 – Check subscription status
- [ ] **1.1** Call `skio_get_subscription_status(email)`
- [ ] **1.2** Get subscription details (ID, status, next order date)

### Step 2 – Ask reason

### Step 3 – Route by reason

#### Route A: "Too many on hand"
- [ ] **3A.1** Offer to skip next order (`skio_skip_next_order_subscription`)
- [ ] **3A.2** If decline: offer 20% discount on next 2 orders
- [ ] **3A.3** If still want to cancel: cancel subscription

#### Route B: "Didn't like quality"
- [ ] **3B.1** Offer product swap (use `shopify_get_product_recommendations`)
- [ ] **3B.2** If decline: cancel subscription

#### Route C: Billing issue
- [ ] **3C.1** Double charge / unexpected charge → Escalate to Monica

#### Route D: Credit card update
- [ ] **3D.1** Escalate to Monica (can't update CC via API)

#### Route E: Pause request
- [ ] **3E.1** Use `skio_pause_subscription` with requested date

---

## Example intents (must route to subscription)

- "I want to cancel my subscription."
- "Can I skip my next order?"
- "I have too many patches on hand."
- "My credit card was charged twice."
- "I want to pause my subscription for a month."

---

## Tool usage (required)

| Tool | When |
|------|------|
| `skio_get_subscription_status` | Step 1 – lookup subscription |
| `skio_skip_next_order_subscription` | Route A – skip offer |
| `shopify_create_discount_code` | Route A – 20% retention discount |
| `shopify_get_product_recommendations` | Route B – product swap |
| `skio_cancel_subscription` | Routes A, B – final cancellation |
| `skio_pause_subscription` | Route E – pause request |
| `shopify_add_tags` | Tag subscription actions |

---

## Important constraints

- [ ] **Skio tools need subscriptionId** from get_subscription_status response
- [ ] **Always try to retain** before cancelling
- [ ] **Billing issues → immediate escalation**
- [ ] **CC update → escalate** (can't be done via API)

---

## Definition of done

- All tests in `tests/subscription/` pass
- Router sends subscription intents to `subscription` agent
- All retention flows work (skip, discount, product swap)
- Proper escalation for billing/CC issues
- Cancellation only after retention attempts
- Tags applied for all actions
