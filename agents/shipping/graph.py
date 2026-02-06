"""LangGraph-based micro-state machine for the Shipping (WISMO) workflow.

This graph implements the vertical slice of the shipping delay manual:

1. Check the customer's order status via a tool.
2. If the order is in transit, apply the day-of-week "wait promise" logic.
3. If a previous promise has been missed and the order is still not
   delivered, trigger escalation.

The graph operates on the shared `AgentState` TypedDict from
`core.state` and uses `internal_data` to store:

- order_status
- order_id
- tracking_url
- wait_promise_until (ISO date string, e.g. "2026-02-06")
- escalation_summary (optional)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .tools import get_order_status


def _ensure_internal_data(state: AgentState) -> Dict[str, Any]:
    internal = state.get("internal_data") or {}
    # Ensure we always have a place to record tool traces.
    if "tool_traces" not in internal:
        internal["tool_traces"] = []
    state["internal_data"] = internal
    return internal


async def node_check_order_status(state: AgentState) -> AgentState:
    """Fetch the latest order status and store it in `internal_data`.

    This node is purely about **tool interaction** and should not
    generate user-facing text itself.
    """

    internal = _ensure_internal_data(state)

    customer = state.get("customer_info") or {}
    shopify_customer_id = customer.get("shopify_customer_id")

    if not shopify_customer_id:
        # Without a Shopify id we cannot proceed reliably. Escalate
        # immediately and let a human resolve the identifier mismatch.
        state["is_escalated"] = True
        state["escalated_at"] = datetime.utcnow()
        internal["escalation_summary"] = EscalationSummary(
            reason="missing_shopify_id",
            details={"customer_info": customer},
        ).model_dump()

        messages = list(state.get("messages", []))
        messages.append(
            Message(
                role="assistant",
                content=(
                    "I couldn't locate your order automatically because some "
                    "account details are missing. I'm looping in Monica, our "
                    "Head of CS, who will take it from here."
                ),
            )
        )
        state["messages"] = messages
        state["workflow_step"] = "escalated_missing_id"
        return state

    tool_resp = await get_order_status(shopify_customer_id=shopify_customer_id)

    # Record tool call for observability.
    internal.setdefault("tool_traces", []).append(
        {
            "name": "get_order_status",
            "inputs": {"shopify_customer_id": shopify_customer_id},
            "output": tool_resp.model_dump(),
        }
    )

    if not tool_resp.success:
        # Tool failure – safest is to escalate.
        state["is_escalated"] = True
        state["escalated_at"] = datetime.utcnow()
        internal["escalation_summary"] = EscalationSummary(
            reason="order_lookup_failed",
            details={"error": tool_resp.error or "unknown"},
        ).model_dump()

        messages = list(state.get("messages", []))
        messages.append(
            Message(
                role="assistant",
                content=(
                    "I'm having trouble fetching your order details right now. "
                    "To make sure this is handled correctly, I'm looping in "
                    "Monica, our Head of CS, who will take it from here."
                ),
            )
        )
        state["messages"] = messages
        state["workflow_step"] = "escalated_tool_error"
        return state

    data = tool_resp.data
    internal["order_id"] = data.get("order_id")
    internal["order_status"] = data.get("status")
    internal["tracking_url"] = data.get("tracking_url")

    state["workflow_step"] = "checked_status"
    return state


async def node_decide_wait_or_escalate(state: AgentState) -> AgentState:
    """Apply wait-promise rules or escalate based on current state.

    This node also appends the user-facing assistant message describing
    the outcome.
    """

    internal = _ensure_internal_data(state)
    messages = list(state.get("messages", []))

    status = (internal.get("order_status") or "").upper()
    order_id = internal.get("order_id", "your order")
    tracking_url = internal.get("tracking_url")

    # 1) Handle already escalated state defensively
    if state.get("is_escalated"):
        # Do not generate new actions; just remind that a human is handling it.
        messages.append(
            Message(
                role="assistant",
                content=(
                    "I've already looped in Monica, our Head of CS, and "
                    "she'll continue handling this conversation."
                ),
            )
        )
        state["messages"] = messages
        state["workflow_step"] = "already_escalated"
        return state

    # 2) Check for missed promise
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
        # Promise window has passed and order still not delivered -> escalate.
        state["is_escalated"] = True
        state["escalated_at"] = datetime.utcnow()
        internal["escalation_summary"] = EscalationSummary(
            reason="wismo_missed_promise",
            details={
                "order_id": order_id,
                "status": status,
                "wait_promise_until": wait_promise_str,
            },
        ).model_dump()

        messages.append(
            Message(
                role="assistant",
                content=(
                    "Thanks for your patience. Since the delivery window we "
                    "promised has passed and your order still isn't marked as "
                    "delivered, I'm looping in Monica, our Head of CS, who "
                    "will take it from here."
                ),
            )
        )
        state["messages"] = messages
        state["workflow_step"] = "escalated_missed_promise"
        return state

    # 3) No missed promise – explain current status and, if in transit,
    #    set a new wait promise.
    base_prefix = f"Order {order_id} " if order_id else "Your order "

    if status == "UNFULFILLED":
        messages.append(
            Message(
                role="assistant",
                content=(
                    base_prefix
                    + "has not shipped yet. As soon as it leaves our warehouse, "
                    "you'll receive an update with tracking details."
                ),
            )
        )
        state["workflow_step"] = "explained_unfulfilled"

    elif status == "DELIVERED":
        messages.append(
            Message(
                role="assistant",
                content=(
                    base_prefix
                    + "is marked as delivered. If that doesn't match what "
                    "you're seeing, please let me know and we can look "
                    "into it further."
                ),
            )
        )
        state["workflow_step"] = "explained_delivered"

    else:  # IN_TRANSIT or anything else treated as in transit
        weekday = today.weekday()  # 0 = Monday

        if 0 <= weekday <= 2:  # Mon–Wed
            # Promise until Friday of this week.
            days_until_friday = 4 - weekday
            promise_date = today + timedelta(days=days_until_friday)
            human_phrase = "Friday"
        else:  # Thu–Sun
            # Promise until early next week -> upcoming Monday
            days_until_monday = (7 - weekday) % 7 or 7
            promise_date = today + timedelta(days=days_until_monday)
            human_phrase = "early next week"

        internal["wait_promise_until"] = promise_date.isoformat()

        tracking_sentence = (
            f" You can track it here: {tracking_url}." if tracking_url else ""
        )

        messages.append(
            Message(
                role="assistant",
                content=(
                    base_prefix
                    + "is on the way. Based on the current status, I'd ask you "
                    f"to give it until {human_phrase}. If it still hasn't "
                    "arrived by then, reply to this email so we can fix it "
                    "for you." + tracking_sentence
                ),
            )
        )
        state["workflow_step"] = "wait_promise_set"

    state["messages"] = messages
    return state


def build_shipping_graph() -> Any:
    """Create and compile the LangGraph for the Shipping workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("check_status", node_check_order_status)
    graph.add_node("decide_wait_or_escalate", node_decide_wait_or_escalate)

    graph.set_entry_point("check_status")
    graph.add_edge("check_status", "decide_wait_or_escalate")
    graph.add_edge("decide_wait_or_escalate", END)

    return graph.compile()


__all__ = ["build_shipping_graph"]
