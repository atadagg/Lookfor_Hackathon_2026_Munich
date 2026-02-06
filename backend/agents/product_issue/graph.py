"""LangGraph-based state machine for Product Issue – No Effect workflow.

Graph structure (first increment)
---------------------------------
    check_order ──┬── [escalated]         ──> END
                  ├── [awaiting_order_id] ──> END  (wait for customer order #)
                  └──> ask_goal ──> END  (workflow_step = awaiting_goal)

Nodes
-----
1. **check_order**  call get_order_and_product; store order_id, order_gid.
   - No email → escalate.
   - Tool fail → escalate.
   - No orders → ask for order number.
   - Success → proceed to ask_goal.
2. **ask_goal**     use GPT to compose empathetic reply asking about goal.
   - Sets workflow_step = "awaiting_goal".
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from schemas.internal import EscalationSummary

from tools import shopify

from .prompts import product_issue_ask_goal_prompt


# ── helpers ────────────────────────────────────────────────────────


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


# ── Node 1 — check order ───────────────────────────────────────────


async def node_check_order(state: AgentState) -> dict:
    """Fetch order via get_order_and_product; store order_id, order_gid."""

    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    customer_email = customer.get("email")

    # ── Path A: no email → escalate ─────────────────────────────────
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

    # ── Path B: lookup by email ─────────────────────────────────────
    try:
        orders_result = await shopify.shopify_get_customer_orders(
            email=customer_email, after="null", limit=10
        )
    except Exception as exc:
        orders_result = {"success": False, "data": {}, "error": str(exc)}

    internal["tool_traces"].append(
        {
            "name": "shopify_get_customer_orders",
            "inputs": {"email": customer_email},
            "output": orders_result,
        }
    )

    if not orders_result.get("success"):
        internal["escalation_summary"] = EscalationSummary(
            reason="order_lookup_failed",
            details={"error": orders_result.get("error", "unknown")},
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

    data = orders_result.get("data") or {}
    orders = data.get("orders", []) if isinstance(data, dict) else []
    if not orders:
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

    latest = orders[0]
    order_name = latest.get("name") or latest.get("id", "")
    if not order_name.startswith("#"):
        order_name = "#%s" % order_name

    try:
        details_result = await shopify.shopify_get_order_details(orderId=order_name)
    except Exception as exc:
        details_result = {"success": False, "data": {}, "error": str(exc)}

    internal["tool_traces"].append(
        {
            "name": "shopify_get_order_details",
            "inputs": {"orderId": order_name},
            "output": details_result,
        }
    )

    if not details_result.get("success"):
        internal["escalation_summary"] = EscalationSummary(
            reason="order_lookup_failed",
            details={"error": details_result.get("error", "unknown")},
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

    d = details_result.get("data") or {}
    if not isinstance(d, dict):
        d = {}
    internal["order_id"] = d.get("name") or order_name
    internal["order_gid"] = d.get("id", "")

    return {
        "internal_data": internal,
        "workflow_step": "checked_order",
    }


# ── Node 2 — ask goal (LLM) ────────────────────────────────────────


async def node_ask_goal(state: AgentState) -> dict:
    """Use GPT to compose empathetic reply asking about customer's goal."""

    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    customer = state.get("customer_info") or {}
    first_name = customer.get("first_name", "")
    order_id = internal.get("order_id", "your order")

    user_msgs = [
        m["content"] for m in state.get("messages", []) if m.get("role") == "user"
    ]
    latest_user = user_msgs[-1] if user_msgs else ""

    context_parts: List[str] = [
        "Customer first name: %s" % first_name if first_name else "",
        "Order ID: %s" % order_id,
        "Customer's complaint: %s" % latest_user,
    ]
    context = "\n".join(p for p in context_parts if p)

    system_prompt = product_issue_ask_goal_prompt()
    user_prompt = (
        "CONTEXT:\n"
        + context
        + "\n\nWrite a short, empathetic reply that asks about their goal "
        "(falling asleep, staying asleep, stress, focus, mosquito protection, etc.). "
        "Include a question mark. Do NOT offer refunds or product swaps yet."
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
        assistant_text = _fallback_ask_goal(first_name)

    new_msg = Message(role="assistant", content=assistant_text)

    return {
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "awaiting_goal",
    }


def _fallback_ask_goal(first_name: str) -> str:
    name = first_name or "there"
    return (
        "I'm sorry to hear the patches aren't helping, %s. "
        "To give you the best advice, could you share what you're hoping to achieve? "
        "For example: falling asleep, staying asleep, stress relief, focus, "
        "or mosquito protection?"
    ) % name


# ── Conditional routing ────────────────────────────────────────────


def _after_check_order(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") == "awaiting_order_id":
        return END
    return "ask_goal"


# ── Graph builder ──────────────────────────────────────────────────


def build_product_issue_graph() -> Any:
    """Create and compile the LangGraph for Product Issue – No Effect."""

    graph = StateGraph(AgentState)

    graph.add_node("check_order", node_check_order)
    graph.add_node("ask_goal", node_ask_goal)

    graph.set_entry_point("check_order")
    graph.add_conditional_edges("check_order", _after_check_order)
    graph.add_edge("ask_goal", END)

    return graph.compile()


# ── ProductIssueAgent class ────────────────────────────────────────


class ProductIssueAgent(BaseAgent):
    """Specialist agent for Product Issue – No Effect workflows."""

    def __init__(self) -> None:
        super().__init__(name="product_issue")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_product_issue_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "product_issue"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["ProductIssueAgent", "build_product_issue_graph"]
