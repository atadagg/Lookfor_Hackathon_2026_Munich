# Positive Feedback (UC6) — Test Roadmap

This document specifies the **MUST-HAVE behavior** for the Positive Feedback use case.

---

## Workflow (from hackathon manual)

### Step 1 – First response (template)
- [ ] **1.1** Use warm, emoji-rich template:
  ```
  Awww 🥰 {{first_name}},
  
  That is so amazing! 🙏 Thank you for that epic feedback!
  
  If it's okay with you, would you mind if I send you a feedback request 
  so you can share your thoughts on NATPAT and our response overall?
  
  It's totally fine if you don't have the time, but I thought I'd ask 
  before sending a feedback request email 😊
  
  Caz
  ```

### Step 2 – If customer says YES
- [ ] **2.1** Send Trustpilot link: https://trustpilot.com/evaluate/naturalpatch.com
- [ ] **2.2** Use template:
  ```
  Awwww, thank you! ❤️
  
  Here's the link to the review page: [link]
  
  Thanks so much! 🙏
  
  Caz xx
  ```

### Step 3 – If customer says NO
- [ ] **3.1** Thank them and wish them well.
- [ ] **3.2** No pressure, positive tone.

### Step 4 – Tagging
- [ ] **4.1** Tag order with "Positive Feedback" (shopify_add_tags).
- [ ] **4.2** Look up orders first (shopify_get_customer_orders).

---

## Example intents (must route to feedback)

- "BuzzPatch saved our camping trip—no bites at all!"
- "The kids LOVE choosing their emoji stickers each night."
- "Focus patches actually helped my son finish homework."
- "OMG! The patches are AMAZING! Thank you!"

---

## Tool usage (required)

| Tool | When |
|------|------|
| `get_customer_latest_order` | Step 4 – order lookup |
| `add_order_tags` | Step 4 – tag "Positive Feedback" |

---

## Style requirements

- [ ] **Emojis**: 🥰 🙏 😊 ❤️ xx ARE expected (not just allowed)
- [ ] **Tone**: Warm, enthusiastic, grateful
- [ ] **No escalation**: Unless unrelated issue

---

## Definition of done

- All tests in `tests/feedback/` pass.
- Router sends positive feedback intents to `feedback` agent.
- First response asks for review permission.
- If yes: send Trustpilot link.
- If no: thank politely.
- Order tagged with "Positive Feedback".
- Emojis present in all responses.
