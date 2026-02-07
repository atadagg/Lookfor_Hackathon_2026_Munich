# Feature Ideas: User-Focused Differentiators & Competitive Edge

Lookfor is already strong on **multi-agent specialization**, **natural-language behavior config**, and **observability**. Below are extra, user-focused features that would make the product stickier for support teams and merchants and harder for competitors to copy.

---

## 1. **Sentiment & Priority Triage** (High impact, medium effort)

**What:** Analyze the **first message** (and optionally the latest) for sentiment and urgency. Surface it in the conversation list and thread header.

**Why it matters:**
- Support teams can sort or filter by "Frustrated" / "Urgent" / "Calm" and tackle hot tickets first.
- Reduces "angry customer waited 4 hours" situations.
- Most tools only show time/status, not *how* the customer feels.

**Implementation sketch:**
- In the router or right after routing: one cheap LLM call (or small classifier) → `sentiment: "frustrated" | "neutral" | "positive"`, `urgency: "high" | "normal" | "low"`.
- Store on thread state; add to `ThreadSummary` and list UI (badge or icon + optional sort/filter).

**Edge:** "We triage by how the customer feels, not just when the ticket arrived."

---

## 2. **Resolution Confidence & "Needs Human" Score** (High impact, medium effort)

**What:** For each **agent reply**, attach a **confidence score** (e.g. 0–1) and a short **reason** ("High – order data matched and policy allows refund" / "Low – customer mentioned legal threat"). Show in the Trace tab and optionally in the Message tab.

**Why it matters:**
- Ops can focus review on low-confidence replies.
- Fewer wrong auto-replies and more trust in the system.
- Competitors rarely expose "how sure the AI was."

**Implementation sketch:**
- In the agent loop, after the final LLM response: one extra small LLM call (or structured output) → `confidence`, `reason_short`.
- Persist in `internal_data` / `agent_turn_history`; surface in UI (e.g. confidence badge next to the reply, expandable reason).

**Edge:** "We show you when the AI is unsure so you can step in before the customer gets a bad answer."

---

## 3. **One-Click Handoff Note for Escalations** (High impact, low effort)

**What:** When an agent escalates, **auto-generate a handoff note** (1–2 sentences) from the existing `escalation_summary` + conversation context. Show it prominently in the thread (e.g. in Trace tab or a dedicated "Handoff" block) and optionally copy-to-clipboard.

**Why it matters:**
- The next human agent knows immediately what happened and what to do.
- You already have `reason`, `internal_summary`; enriching with a single LLM call (e.g. "Summarize for handoff: reason, last customer ask, recommended action") makes it human-ready.

**Implementation sketch:**
- When `is_escalated` is set, optionally call a small LLM to produce `handoff_note: string` from `escalation_summary` + last few messages.
- Add `handoff_note` to thread state / API; in the frontend, show a "Handoff note" card with a copy button.

**Edge:** "Escalations come with a ready-made handoff note so your team doesn’t waste time reading the whole thread."

---

## 4. **Suggested Reply (Human-in-the-Loop)** (Very high impact, higher effort)

**What:** For **human agents** (or before sending the final message), show an **AI-suggested reply**: "Agent suggests: [draft]. [Edit] [Approve & send] [Escalate]."

**Why it matters:**
- Speeds up human agents while keeping them in control.
- Great for hybrid workflows: AI proposes, human approves or edits.
- Differentiator vs pure chatbots and vs pure manual reply.

**Implementation sketch:**
- New endpoint or step: given thread + latest customer message, call the same agent (or a dedicated "suggest_reply" prompt) to produce a **draft reply** without persisting it. Return draft to frontend.
- UI: "Suggested reply" card with textarea (editable), buttons [Edit] [Approve & send] [Escalate]. On Approve, send the (possibly edited) message and persist.

**Edge:** "Your team can send in seconds by approving or lightly editing the AI suggestion instead of typing from scratch."

---

## 5. **Brand Voice / Tone Slider** (Medium impact, low effort)

**What:** In MAS Behavior (or a small "Brand" section), let the merchant choose **tone**: e.g. "More formal" / "Friendly" / "Minimal (short answers)." Inject one line into all agent system prompts.

**Why it matters:**
- Same logic, different brand feel—no editing YAML or prompts.
- Merchants care a lot about "sounding like us."

**Implementation sketch:**
- Add `brand_tone: "formal" | "friendly" | "minimal"` to MAS config (or a separate tiny config). In `inject_policies_into_prompt`, append one sentence (e.g. "Use a friendly, conversational tone.").
- Optional: expose in Behavior sidebar as a dropdown.

**Edge:** "One setting to match your brand voice across all agents."

---

## 6. **Customer History Snippet in Thread** (Medium impact, medium effort)

**What:** In the **thread header** (or a collapsible section), show a one-liner: "This customer: 2 refunds, 1 WISMO in the last 6 months" (from Shopify/Skio or from your own thread history).

**Why it matters:**
- Human agents (and future agent logic) can avoid offering a 3rd refund when policy says "max 2."
- Builds trust: "The system knows the full picture."

**Implementation sketch:**
- Aggregate by `customer_email` (or shopify_customer_id): count threads by intent/routed_agent and time window. Either from your DB or from a Shopify/Skio API if available.
- Add `customer_history_snippet: string` to thread state or a dedicated API; show in conversation detail header.

**Edge:** "We show every agent the customer’s support history at a glance."

---

## 7. **Proactive Outreach Hooks** (High impact, higher effort)

**What:** When **external events** happen (e.g. tracking updated for a WISMO ticket, or subscription renewed), trigger a **suggested proactive message** (e.g. "Tracking just updated. Send this to the customer? [Yes] [Edit] [No]").

**Why it matters:**
- Reduces "where’s my order?" follow-ups and improves perceived care.
- Positions you as "proactive support" not just "reactive bot."

**Implementation sketch:**
- Requires event ingestion (webhooks from Shopify/Skio for fulfillment/tracking/subscription events). Match event → thread (e.g. by order_id). Generate one short proactive message; surface in dashboard as "Suggested outreach" or in-thread.

**Edge:** "We suggest when to reach out before the customer has to ask again."

---

## Quick Wins vs Bigger Bets

| Feature                     | Impact   | Effort   | Suggested order |
|----------------------------|----------|----------|------------------|
| Handoff note for escalations | High     | Low      | 1st              |
| Brand voice / tone         | Medium   | Low      | 2nd              |
| Sentiment & priority       | High     | Medium   | 3rd              |
| Resolution confidence      | High     | Medium   | 4th              |
| Customer history snippet   | Medium   | Medium   | 5th              |
| Suggested reply (human-in-the-loop) | Very high | Higher | 6th              |
| Proactive outreach         | High     | Higher   | 7th              |

---

## Summary

- **Immediate edge:** Handoff note + brand tone (low effort, clear value).
- **Trust & control:** Sentiment triage + resolution confidence (ops see "who’s upset" and "when the AI is unsure").
- **Product vision:** Suggested reply (human-in-the-loop) and proactive outreach (from reactive to proactive support).

These features are user-focused (support agents and merchants), leverage the multi-agent + MAS setup you already have, and are the kind of differentiators that are hard for generic "AI chat" products to replicate.
