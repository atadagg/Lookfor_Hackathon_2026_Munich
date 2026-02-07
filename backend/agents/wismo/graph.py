"""LangGraph-based state machine for the WISMO workflow.

Graph structure
---------------
    check_status ──┬── [escalated]         ──> END
                   ├── [awaiting_order_id]  ──> END  (wait for customer reply)
                   └──> decide_action ──┬── [escalated] ──> END
                                        └──> generate_response ──> END

Nodes
-----
1. **check_status**         call the order-status tool; store results.
   - If no order found → ask the customer for their order number.
   - If resuming from ``awaiting_order_id`` → extract order # from
     the latest message and retry the lookup.
2. **decide_action**        apply wait-promise / escalation rules (deterministic).
3. **generate_response**    use GPT to compose a natural customer reply.

All nodes return *partial* state dicts so LangGraph can merge them
cleanly (no ``add_messages`` reducer — we manage the messages list
ourselves).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.mas_behavior import inject_policies_into_prompt
from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .prompts import wismo_system_prompt
from .tools import (
    extract_order_id,
    get_order_by_id,
    get_order_status,
)


# ── helpers ────────────────────────────────────────────────────────


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    """Copy ``internal_data`` and make sure ``tool_traces`` exists."""
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


def _latest_user_text(state: AgentState) -> str:
    """Return the content of the most recent user message."""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# ── Node 1 — check order status ───────────────────────────────────


async def node_check_order_status(state: AgentState) -> dict:
    """Fetch the latest order status via the tool and store it.

    Handles three paths:
    * Normal first call — look up by customer email.
    * Resuming after ``awaiting_order_id`` — extract order # from the
      latest user message and call ``get_order_by_id``.
    * No orders found — ask the customer for their order number.
    """

    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    customer_email = customer.get("email")
    prev_step = state.get("workflow_step") or ""

    # ── Path A: resuming after we asked for an order ID ────────────
    if prev_step == "awaiting_order_id":
        latest_text = _latest_user_text(state)
        extracted_id = extract_order_id(latest_text)

        if not extracted_id:
            ask_count = internal.get("_order_id_ask_count", 1)
            if ask_count >= 2:
                internal["escalation_summary"] = EscalationSummary(
                    reason="order_id_not_provided",
                    details={"latest_message": latest_text},
                ).model_dump()
                new_msg = Message(
                    role="assistant",
                    content=(
                        "I still couldn't find an order number in your message. "
                        "To make sure you get the right support, I'm looping in "
                        "Monica, our Head of CS, who will take it from here."
                    ),
                )
                return {
                    "is_escalated": True,
                    "escalated_at": datetime.now(timezone.utc),
                    "internal_data": internal,
                    "messages": list(state.get("messages", [])) + [new_msg],
                    "workflow_step": "escalated_no_order_id",
                }

            internal["_order_id_ask_count"] = ask_count + 1
            new_msg = Message(
                role="assistant",
                content=(
                    "I couldn't spot an order number in your message. "
                    "Could you share it? It usually looks like #12345 or NP12345."
                ),
            )
            return {
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "awaiting_order_id",
            }

        # We have an order ID — look it up directly
        tool_resp = await get_order_by_id(order_id=extracted_id)

        internal["tool_traces"].append(
            {
                "name": "get_order_by_id",
                "inputs": {"order_id": extracted_id},
                "output": tool_resp.model_dump(),
            }
        )

        if not tool_resp.success:
            internal["escalation_summary"] = EscalationSummary(
                reason="order_lookup_failed",
                details={"error": tool_resp.error or "unknown", "order_id": extracted_id},
            ).model_dump()
            new_msg = Message(
                role="assistant",
                content=(
                    "I wasn't able to pull up that order. To make sure this "
                    "is handled correctly, I'm looping in Monica, our Head "
                    "of CS, who will take it from here."
                ),
            )
            return {
                "is_escalated": True,
                "escalated_at": datetime.now(timezone.utc),
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "escalated_tool_error",
            }

        data = tool_resp.data
        internal["order_id"] = data.get("order_id")
        internal["order_status"] = data.get("status")
        internal["tracking_url"] = data.get("tracking_url")
        return {
            "internal_data": internal,
            "workflow_step": "checked_status",
        }

    # ── Path B: no email → escalate ───────────────────────────────
    if not customer_email:
        internal["escalation_summary"] = EscalationSummary(
            reason="missing_customer_email",
            details={"customer_info": customer},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I couldn't locate your order automatically because some "
                "account details are missing. I'm looping in Monica, our "
                "Head of CS, who will take it from here."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_missing_email",
        }

    # ── Path C: normal lookup by customer email ────────────────────
    tool_resp = await get_order_status(email=customer_email)

    internal["tool_traces"].append(
        {
            "name": "get_order_status",
            "inputs": {"email": customer_email},
            "output": tool_resp.model_dump(),
        }
    )

    if not tool_resp.success:
        internal["escalation_summary"] = EscalationSummary(
            reason="order_lookup_failed",
            details={"error": tool_resp.error or "unknown"},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I'm having trouble fetching your order details right now. "
                "To make sure this is handled correctly, I'm looping in "
                "Monica, our Head of CS, who will take it from here."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_tool_error",
        }

    # ── Path D: tool succeeded but no orders found ─────────────────
    if tool_resp.data.get("no_orders"):
        internal["_order_id_ask_count"] = 1
        new_msg = Message(
            role="assistant",
            content=(
                "I couldn't find any recent orders under your account. "
                "Could you share your order number so I can look it up? "
                "It usually looks like #12345 or NP12345."
            ),
        )
        return {
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "awaiting_order_id",
        }

    # ── Path E: order found — store details ────────────────────────
    data = tool_resp.data
    internal["order_id"] = data.get("order_id")
    internal["order_status"] = data.get("status")
    internal["tracking_url"] = data.get("tracking_url")

    return {
        "internal_data": internal,
        "workflow_step": "checked_status",
    }


# ── Node 2 — decide action (deterministic) ────────────────────────


async def node_decide_wait_or_escalate(state: AgentState) -> dict:
    """Apply the WISMO wait-promise / escalation rules."""

    internal = _fresh_internal(state)
    status = (internal.get("order_status") or "").upper()
    order_id = internal.get("order_id", "your order")

    if state.get("is_escalated"):
        return {"workflow_step": "already_escalated"}

    # -- Missed-promise check -----------------------------------------
    wait_promise_str = internal.get("wait_promise_until")
    today = date.today()

    if wait_promise_str:
        try:
            promised_date = date.fromisoformat(wait_promise_str)
        except ValueError:
            promised_date = None
    else:
        promised_date = None

    if promised_date and today > promised_date and status != "DELIVERED":
        internal["escalation_summary"] = EscalationSummary(
            reason="wismo_missed_promise",
            details={
                "order_id": order_id,
                "status": status,
                "wait_promise_until": wait_promise_str,
            },
        ).model_dump()

        new_msg = Message(
            role="assistant",
            content=(
                "Thanks for your patience. Since the delivery window we "
                "promised has passed and your order still isn't marked as "
                "delivered, I'm looping in Monica, our Head of CS, who "
                "will take it from here and process a free resend for you."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_missed_promise",
        }

    # -- No escalation — decide the right action ---------------------
    if status == "UNFULFILLED":
        internal["decided_action"] = "explain_unfulfilled"
    elif status == "DELIVERED":
        internal["decided_action"] = "explain_delivered"
    else:
        weekday = today.weekday()
        if 0 <= weekday <= 2:
            days_until_friday = 4 - weekday
            promise_date = today + timedelta(days=days_until_friday)
            internal["promise_day_label"] = "Friday"
        else:
            days_until_monday = (7 - weekday) % 7 or 7
            promise_date = today + timedelta(days=days_until_monday)
            internal["promise_day_label"] = "early next week"
        internal["wait_promise_until"] = promise_date.isoformat()
        internal["decided_action"] = "wait_promise"

    return {
        "internal_data": internal,
        "workflow_step": "action_decided",
    }


# ── Node 3 — generate customer response (LLM) ────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Use GPT-4o-mini to compose a natural, concise customer reply."""

    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    customer = state.get("customer_info") or {}
    first_name = customer.get("first_name", "")

    action = internal.get("decided_action", "")
    order_id = internal.get("order_id", "your order")
    tracking_url = internal.get("tracking_url")
    promise_label = internal.get("promise_day_label", "")
    status = internal.get("order_status", "")

    context_parts: List[str] = [
        "Customer first name: %s" % first_name if first_name else "",
        "Order ID: %s" % order_id,
        "Current order status: %s" % status,
        "Tracking URL: %s" % tracking_url if tracking_url else "Tracking URL: not available",
        "Decided action: %s" % action,
    ]
    if action == "wait_promise":
        context_parts.append("Wait-promise day: %s" % promise_label)
        context_parts.append(
            "Wait-promise date: %s" % internal.get("wait_promise_until", "")
        )

    context = "\n".join(p for p in context_parts if p)
    user_msgs = [
        m["content"] for m in state.get("messages", []) if m.get("role") == "user"
    ]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = inject_policies_into_prompt(wismo_system_prompt(), agent="wismo")
    user_prompt = (
        "CONTEXT (from tools and workflow rules):\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a concise, friendly reply (2-3 sentences). "
        "Follow the WISMO workflow rules strictly. Do NOT invent information "
        "not present in the context above. Include the tracking URL only if "
        "the order is in transit. Do NOT include a subject line."
    )

    try:
        client = get_async_openai_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        assistant_text = (resp.choices[0].message.content or "").strip()
        if not assistant_text:
            raise ValueError("Empty LLM response")
    except Exception:
        assistant_text = _fallback_response(
            action, order_id, tracking_url, promise_label
        )

    new_msg = Message(role="assistant", content=assistant_text)
    step = _step_for_action(action)

    return {
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": step,
    }


# ── Fallback templates ─────────────────────────────────────────────


def _fallback_response(
    action: str, order_id: str, tracking_url: Optional[str], promise_label: str,
) -> str:
    prefix = "Order %s" % order_id if order_id else "Your order"

    if action == "explain_unfulfilled":
        return (
            "%s has not shipped yet. As soon as it leaves our warehouse, "
            "you'll receive an update with tracking details." % prefix
        )
    if action == "explain_delivered":
        return (
            "%s is marked as delivered. If that doesn't match what "
            "you're seeing, please let me know and we can look into it further."
            % prefix
        )
    tracking = (
        " You can track it here: %s" % tracking_url if tracking_url else ""
    )
    return (
        "%s is on the way. Based on the current status, I'd ask you "
        "to give it until %s. If it still hasn't arrived by then, "
        "reply to this email so we can fix it for you.%s"
        % (prefix, promise_label, tracking)
    )


def _step_for_action(action: str) -> str:
    return {
        "explain_unfulfilled": "explained_unfulfilled",
        "explain_delivered": "explained_delivered",
    }.get(action, "wait_promise_set")


# ── Conditional routing ────────────────────────────────────────────


def _after_check_status(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") == "awaiting_order_id":
        return END
    return "decide_action"


def _after_decide_action(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    return "generate_response"


# ── Graph builder ──────────────────────────────────────────────────


def build_wismo_graph() -> Any:
    """Create and compile the LangGraph for the WISMO workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("check_status", node_check_order_status)
    graph.add_node("decide_action", node_decide_wait_or_escalate)
    graph.add_node("generate_response", node_generate_response)

    graph.set_entry_point("check_status")
    graph.add_conditional_edges("check_status", _after_check_status)
    graph.add_conditional_edges("decide_action", _after_decide_action)
    graph.add_edge("generate_response", END)

    return graph.compile()


# ── WismoAgent class ───────────────────────────────────────────────


class WismoAgent(BaseAgent):
    """Specialist agent for Shipping Delay / WISMO workflows."""

    def __init__(self) -> None:
        super().__init__(name="wismo")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_wismo_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "shipping"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["WismoAgent", "build_wismo_graph"]
