"""LangGraph state machine for Refund Request workflow.

Graph structure
--------------
    check_order ──┬── [escalated]         ──> END
                  ├── [awaiting_order_id] ──> END
                  └──> decide_action ──┬── [awaiting / escalated] ──> END
                                        └──> generate_response ──> END

Nodes
-----
1. check_order       Get customer's latest order; store order_id, order_gid, status.
2. decide_action     Route by refund reason; execute credit/refund or escalate.
3. generate_response Compose reply with refund_system_prompt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .prompts import refund_system_prompt
from .tools import (
    add_order_tags,
    cancel_order,
    create_store_credit,
    get_customer_latest_order,
    refund_order_cash,
)


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


def _latest_user_text(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# ── Node 1 — check order ───────────────────────────────────────────


async def node_check_order(state: AgentState) -> dict:
    """Fetch customer's latest order and store details."""
    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    customer_email = customer.get("email")

    if not customer_email:
        internal["escalation_summary"] = EscalationSummary(
            reason="missing_customer_email",
            details={"customer_info": customer},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I couldn't locate your order automatically. I'm looping in "
                "Monica, our Head of CS, who will take it from here."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_missing_email",
        }

    resp = await get_customer_latest_order(email=customer_email)
    internal["tool_traces"].append({
        "name": "get_customer_latest_order",
        "inputs": {"email": customer_email},
        "output": resp.model_dump(),
    })

    if not resp.success:
        internal["escalation_summary"] = EscalationSummary(
            reason="order_lookup_failed",
            details={"error": resp.error or "unknown"},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I'm having trouble fetching your order. I'm looping in "
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

    if resp.data.get("no_orders"):
        internal["escalation_summary"] = EscalationSummary(
            reason="no_orders_found",
            details={},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I couldn't find any orders under your account. "
                "I'm looping in Monica, our Head of CS, who will help you out."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_no_orders",
        }

    data = resp.data
    internal["order_id"] = data.get("order_id")
    internal["order_gid"] = data.get("order_gid")
    internal["customer_gid"] = data.get("customer_gid")
    internal["order_status"] = data.get("status")
    return {"internal_data": internal, "workflow_step": "checked_order"}


# ── Node 2 — decide action ─────────────────────────────────────────


async def node_decide_action(state: AgentState) -> dict:
    """Route by refund reason; execute store credit/refund or escalate."""
    internal = _fresh_internal(state)
    if state.get("is_escalated"):
        return {"workflow_step": "already_escalated"}

    latest = _latest_user_text(state).lower()
    order_gid = internal.get("order_gid", "")
    customer_gid = internal.get("customer_gid", "")
    order_status = internal.get("order_status", "")

    # Detect if they're choosing store credit or cash refund
    wants_store_credit = any(word in latest for word in ("store credit", "credit", "yes to credit"))
    wants_cash_refund = any(word in latest for word in ("cash", "refund", "money back", "no to credit"))

    # Execute store credit
    if wants_store_credit and customer_gid:
        amount = "10.00"  # Could be derived from order
        credit_resp = await create_store_credit(
            customer_gid=customer_gid,
            amount=amount,
            currency_code="USD",
            expires_at=None,
        )
        internal["tool_traces"].append({
            "name": "create_store_credit",
            "inputs": {"customer_gid": customer_gid, "amount": amount},
            "output": credit_resp.model_dump(),
        })
        if credit_resp.success:
            tag_resp = await add_order_tags(order_gid=order_gid, tags=["Refund – Store Credit Issued"])
            internal["tool_traces"].append({
                "name": "add_order_tags",
                "inputs": {"order_gid": order_gid, "tags": ["Refund – Store Credit Issued"]},
                "output": tag_resp.model_dump(),
            })
        internal["decided_action"] = "issued_store_credit"
        internal["store_credit_amount"] = amount
        return {"internal_data": internal, "workflow_step": "execute_done"}

    # Execute cash refund
    if wants_cash_refund and order_gid:
        # If unfulfilled, cancel; else refund
        if order_status == "UNFULFILLED":
            cancel_resp = await cancel_order(order_gid=order_gid, reason="CUSTOMER")
            internal["tool_traces"].append({
                "name": "cancel_order",
                "inputs": {"order_gid": order_gid, "reason": "CUSTOMER"},
                "output": cancel_resp.model_dump(),
            })
            internal["decided_action"] = "cancelled_and_refunded"
        else:
            refund_resp = await refund_order_cash(order_gid=order_gid)
            internal["tool_traces"].append({
                "name": "refund_order_cash",
                "inputs": {"order_gid": order_gid},
                "output": refund_resp.model_dump(),
            })
            tag_resp = await add_order_tags(order_gid=order_gid, tags=["Refund – Cash Refund Issued"])
            internal["tool_traces"].append({
                "name": "add_order_tags",
                "inputs": {"order_gid": order_gid, "tags": ["Refund – Cash Refund Issued"]},
                "output": tag_resp.model_dump(),
            })
            internal["decided_action"] = "issued_cash_refund"
        return {"internal_data": internal, "workflow_step": "execute_done"}

    # Detect refund reason
    reason_expectations = any(word in latest for word in ("didn't work", "not effective", "expectations", "doesn't work"))
    reason_shipping = any(word in latest for word in ("shipping", "delay", "hasn't arrived", "not here"))
    reason_damaged = any(word in latest for word in ("damaged", "wrong", "defective", "broken"))
    reason_changed_mind = any(word in latest for word in ("changed mind", "don't want", "don't need"))

    # Route A: Product didn't meet expectations → offer swap, then store credit, then cash
    if reason_expectations:
        if not internal.get("offered_swap"):
            new_msg = Message(
                role="assistant",
                content=(
                    "I'm sorry to hear that. Before we process a refund, would you like to try "
                    "a different product that might work better for your needs? Otherwise, I can "
                    "offer you store credit with a 10% bonus, or a full refund."
                ),
            )
            internal["offered_swap"] = True
            return {
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "offered_swap",
            }
        # Fall through to offer credit/refund

    # Route B: Shipping delay → escalate for replacement
    if reason_shipping:
        internal["escalation_summary"] = EscalationSummary(
            reason="shipping_delay_replacement",
            details={"order_gid": order_gid},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I'm sorry your order is delayed. Let me loop in Monica, our Head of CS, "
                "who can arrange a free replacement for you."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_shipping_delay",
        }

    # Route C: Damaged or wrong item → offer replacement or store credit → escalate
    if reason_damaged:
        internal["escalation_summary"] = EscalationSummary(
            reason="damaged_wrong_item_replacement",
            details={"order_gid": order_gid},
        ).model_dump()
        new_msg = Message(
            role="assistant",
            content=(
                "I'm so sorry about that. Let me loop in Monica, our Head of CS, "
                "who can arrange a free replacement or issue store credit for you."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_damaged_wrong",
        }

    # Route D: Changed mind → cancel if unfulfilled, else store credit then cash
    if reason_changed_mind:
        if order_status == "UNFULFILLED":
            cancel_resp = await cancel_order(order_gid=order_gid, reason="CUSTOMER")
            internal["tool_traces"].append({
                "name": "cancel_order",
                "inputs": {"order_gid": order_gid, "reason": "CUSTOMER"},
                "output": cancel_resp.model_dump(),
            })
            tag_resp = await add_order_tags(order_gid=order_gid, tags=["Refund – Changed Mind, Cancelled"])
            internal["tool_traces"].append({
                "name": "add_order_tags",
                "inputs": {"order_gid": order_gid, "tags": ["Refund – Changed Mind, Cancelled"]},
                "output": tag_resp.model_dump(),
            })
            internal["decided_action"] = "cancelled_changed_mind"
            return {"internal_data": internal, "workflow_step": "execute_done"}
        # Else fall through to offer credit/refund

    # Default: ask for reason or offer store credit first, then cash
    if not internal.get("asked_for_reason"):
        new_msg = Message(
            role="assistant",
            content=(
                "I can help with that. Could you let me know why you'd like a refund? "
                "(Product didn't work as expected, shipping delay, damaged/wrong item, changed your mind, etc.)"
            ),
        )
        internal["asked_for_reason"] = True
        return {
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "awaiting_refund_reason",
        }

    # Offer store credit first, then cash
    new_msg = Message(
        role="assistant",
        content=(
            "I can offer you store credit with a 10% bonus, or process a full refund to your "
            "original payment method. Which would you prefer?"
        ),
    )
    internal["offered_choice"] = True
    return {
        "internal_data": internal,
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "offered_credit_or_refund",
    }


# ── Node 3 — generate response ─────────────────────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Compose a natural reply using refund_system_prompt and context."""
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    customer = state.get("customer_info") or {}
    first_name = customer.get("first_name", "")
    action = internal.get("decided_action", "")
    order_id = internal.get("order_id", "your order")

    context_parts: List[str] = [
        "Customer first name: %s" % first_name if first_name else "",
        "Order ID: %s" % order_id,
        "Decided action: %s" % action,
    ]
    if action == "issued_store_credit":
        context_parts.append("Store credit amount: %s" % internal.get("store_credit_amount", ""))
    context = "\n".join(p for p in context_parts if p)
    user_msgs = [m["content"] for m in state.get("messages", []) if m.get("role") == "user"]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = refund_system_prompt()
    user_prompt = (
        "CONTEXT:\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a concise, helpful reply (2-4 sentences). "
        "Do NOT include a subject line."
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
        assistant_text = _fallback_response(action, order_id)

    new_msg = Message(role="assistant", content=assistant_text)
    return {
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "responded",
    }


def _fallback_response(action: str, order_id: str) -> str:
    prefix = "Order %s" % order_id if order_id else "Your order"
    if action == "issued_store_credit":
        return "%s: I've issued store credit. It's available immediately at checkout." % prefix
    if action == "issued_cash_refund":
        return "%s: I've processed your refund. It should appear in a few business days." % prefix
    if action == "cancelled_changed_mind":
        return "%s has been cancelled. You'll receive a refund shortly." % prefix
    if action == "cancelled_and_refunded":
        return "%s has been cancelled and you'll receive a full refund." % prefix
    return "%s: I'm working on your refund request. Let me know if you need anything else." % prefix


# ── Conditional routing ────────────────────────────────────────────


def _after_check_order(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    return "decide_action"


def _after_decide_action(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") in ("awaiting_refund_reason", "offered_swap", "offered_credit_or_refund"):
        return END
    if state.get("workflow_step") == "execute_done":
        return "generate_response"
    return END


# ── Graph builder ──────────────────────────────────────────────────


def build_refund_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("check_order", node_check_order)
    graph.add_node("decide_action", node_decide_action)
    graph.add_node("generate_response", node_generate_response)
    graph.set_entry_point("check_order")
    graph.add_conditional_edges("check_order", _after_check_order)
    graph.add_conditional_edges("decide_action", _after_decide_action)
    graph.add_edge("generate_response", END)
    return graph.compile()


# ── RefundAgent class ──────────────────────────────────────────────


class RefundAgent(BaseAgent):
    """Specialist agent for Refund Request workflows."""

    def __init__(self) -> None:
        super().__init__(name="refund")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_refund_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "refund"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["RefundAgent", "build_refund_graph"]
