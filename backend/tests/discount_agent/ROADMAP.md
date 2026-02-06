# Discount Code Request (UC8) — Test Roadmap

This document specifies the **MUST-HAVE behavior** for Discount Code Request.

---

## Workflow (from hackathon manual)

### Step 1 – Check if code already created
- [ ] **1.1** Check `internal_data.code_created`.
- [ ] **1.2** If already created: don't create duplicate.

### Step 2 – Create 10% discount code
- [ ] **2.1** Call `shopify_create_discount_code`.
- [ ] **2.2** Code format: `NATPAT10-{random}`.
- [ ] **2.3** 10% off, single use.

### Step 3 – Respond with code
- [ ] **3.1** Include the discount code in reply.
- [ ] **3.2** Explain how to use at checkout.
- [ ] **3.3** Mention single-use limitation.

---

## Example intents (must route to discount_agent)

- "Can I get a discount code?"
- "Do you have any promo codes available?"
- "Is there a coupon I can use?"
- "Can you send me a discount?"

---

## Tool usage (required)

| Tool | When |
|------|------|
| `create_discount_10_percent` | Step 2 – create discount code |

---

## Important constraints

- [ ] **No duplicates**: Don't create multiple codes for same conversation.
- [ ] **Single-use**: Code works once per customer.
- [ ] **10% off**: Fixed percentage.

---

## Definition of done

- All tests in `tests/discount_agent/` pass.
- Router sends "discount" intents to `discount_agent`.
- Agent creates 10% discount code (shopify_create_discount_code).
- Code format: `NATPAT10-{random}`.
- No duplicate codes per conversation.
- Clear instructions provided.
