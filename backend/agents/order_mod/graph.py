"""LangGraph state machine for Order Modification workflow.

Graph structure
--------------
    check_order ──┬── [escalated]         ──> END
                  ├── [awaiting_order_id] ──> END
                  └──> decide_action ──┬── [awaiting / escalated] ──> END
                                        └──> generate_response ──> END

Nodes
-----
1. check_order     Get customer's latest order; store order_id, order_gid, status, created_at.
2. decide_action   Classify intent (cancel vs address update); execute or ask for details.
3. generate_response  Compose reply with order_mod_system_prompt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .prompts import order_mod_system_prompt
from .tools import (
    add_order_tags,
    cancel_order,
    get_customer_latest_order,
    update_shipping_address,
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
    internal["order_status"] = data.get("status")
    internal["order_created_at"] = data.get("created_at")
    return {"internal_data": internal, "workflow_step": "checked_order"}


# ── Node 2 — decide action ─────────────────────────────────────────


async def node_decide_action(state: AgentState) -> dict:
    """Classify intent (cancel vs address); execute or ask for details."""
    internal = _fresh_internal(state)
    if state.get("is_escalated"):
        return {"workflow_step": "already_escalated"}

    latest = _latest_user_text(state).lower()
    order_gid = internal.get("order_gid", "")
    order_status = internal.get("order_status", "")

    # Detect intent
    is_cancel = any(word in latest for word in ("cancel", "cancellation", "don't want"))
    is_address = any(word in latest for word in ("address", "wrong address", "ship to"))

    # CANCEL FLOW
    if is_cancel:
        # If not unfulfilled, can't cancel
        if order_status != "UNFULFILLED":
            internal["escalation_summary"] = EscalationSummary(
                reason="order_already_fulfilled",
                details={"order_status": order_status},
            ).model_dump()
            new_msg = Message(
                role="assistant",
                content=(
                    "Your order has already been fulfilled, so I can't cancel it. "
                    "I'm looping in Monica, our Head of CS, who can help with alternatives."
                ),
            )
            return {
                "is_escalated": True,
                "escalated_at": datetime.now(timezone.utc),
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "escalated_fulfilled",
            }

        # If accidental order mentioned, cancel immediately
        if "accidental" in latest or "by mistake" in latest:
            cancel_resp = await cancel_order(
                order_gid=order_gid,
                reason="CUSTOMER",
                staff_note="Accidental order",
            )
            internal["tool_traces"].append({
                "name": "cancel_order",
                "inputs": {"order_gid": order_gid, "reason": "CUSTOMER"},
                "output": cancel_resp.model_dump(),
            })
            if cancel_resp.success:
                tag_resp = await add_order_tags(order_gid=order_gid, tags=["Accidental Order – Cancelled"])
                internal["tool_traces"].append({
                    "name": "add_order_tags",
                    "inputs": {"order_gid": order_gid, "tags": ["Accidental Order – Cancelled"]},
                    "output": tag_resp.model_dump(),
                })
            internal["decided_action"] = "cancelled_order"
            return {"internal_data": internal, "workflow_step": "execute_done"}

        # Ask why they want to cancel
        if not internal.get("cancel_reason_asked"):
            new_msg = Message(
                role="assistant",
                content=(
                    "I can help with that. Could you let me know why you'd like to cancel? "
                    "(Shipping delay, changed your mind, accidental order, etc.)"
                ),
            )
            internal["cancel_reason_asked"] = True
            return {
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "awaiting_cancel_reason",
            }

        # Proceed with cancellation
        cancel_resp = await cancel_order(
            order_gid=order_gid,
            reason="CUSTOMER",
            staff_note="Customer requested cancellation",
        )
        internal["tool_traces"].append({
            "name": "cancel_order",
            "inputs": {"order_gid": order_gid, "reason": "CUSTOMER"},
            "output": cancel_resp.model_dump(),
        })
        internal["decided_action"] = "cancelled_order"
        return {"internal_data": internal, "workflow_step": "execute_done"}

    # ADDRESS UPDATE FLOW
    if is_address:
        # Must be unfulfilled
        if order_status != "UNFULFILLED":
            internal["escalation_summary"] = EscalationSummary(
                reason="order_already_fulfilled",
                details={"order_status": order_status},
            ).model_dump()
            new_msg = Message(
                role="assistant",
                content=(
                    "Your order has already been fulfilled, so I can't update the address. "
                    "I'm looping in Monica, our Head of CS, who can help."
                ),
            )
            return {
                "is_escalated": True,
                "escalated_at": datetime.now(timezone.utc),
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "escalated_fulfilled",
            }

        # Ask for new address
        new_msg = Message(
            role="assistant",
            content=(
                "I can help update the shipping address. Please provide the complete new address "
                "(street, city, state, zip, country)."
            ),
        )
        internal["decided_action"] = "ask_for_address"
        return {
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "awaiting_new_address",
        }

    # Default: escalate or ask what they want
    new_msg = Message(
        role="assistant",
        content=(
            "I can help with cancellations or address updates for your order. "
            "Which would you like to do?"
        ),
    )
    return {
        "internal_data": internal,
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "awaiting_intent",
    }


# ── Node 3 — generate response ─────────────────────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Compose a natural reply using order_mod_system_prompt and context."""
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
    context = "\n".join(p for p in context_parts if p)
    user_msgs = [m["content"] for m in state.get("messages", []) if m.get("role") == "user"]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = order_mod_system_prompt()
    user_prompt = (
        "CONTEXT:\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a concise, helpful reply (2-3 sentences). "
        "Do NOT include a subject line."
    )

    try:
        client = get_async_openai_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=128,
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
    if action == "cancelled_order":
        return "%s has been cancelled. You'll receive a refund shortly." % prefix
    if action == "updated_address":
        return "%s shipping address has been updated. It'll ship to the new location." % prefix
    return "%s: I'm working on it. Let me know if you need anything else." % prefix


# ── Conditional routing ────────────────────────────────────────────


def _after_check_order(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    return "decide_action"


def _after_decide_action(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") in ("awaiting_cancel_reason", "awaiting_new_address", "awaiting_intent"):
        return END
    if state.get("workflow_step") == "execute_done":
        return "generate_response"
    return END


# ── Graph builder ──────────────────────────────────────────────────


def build_order_mod_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("check_order", node_check_order)
    graph.add_node("decide_action", node_decide_action)
    graph.add_node("generate_response", node_generate_response)
    graph.set_entry_point("check_order")
    graph.add_conditional_edges("check_order", _after_check_order)
    graph.add_conditional_edges("decide_action", _after_decide_action)
    graph.add_edge("generate_response", END)
    return graph.compile()


# ── OrderModAgent class ────────────────────────────────────────────


class OrderModAgent(BaseAgent):
    """Specialist agent for Order Modification workflows."""

    def __init__(self) -> None:
        super().__init__(name="order_mod")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_order_mod_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "order_modification"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["OrderModAgent", "build_order_mod_graph"]
