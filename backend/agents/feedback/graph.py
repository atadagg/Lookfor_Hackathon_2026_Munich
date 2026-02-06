"""LangGraph state machine for Positive Feedback workflow.

Graph structure
--------------
    check_and_tag ──> generate_response ──> END

Nodes
-----
1. check_and_tag      Look up customer's order and tag it with "Positive Feedback".
2. generate_response  Compose warm reply asking if they'd share a review.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from .prompts import feedback_system_prompt
from .tools import add_order_tags, get_customer_latest_order


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


def _latest_user_text(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# ── Node 1 — check and tag ─────────────────────────────────────────


async def node_check_and_tag(state: AgentState) -> dict:
    """Look up customer's latest order and tag it with 'Positive Feedback'."""
    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    customer_email = customer.get("email")

    # Try to get order and tag it (best effort)
    if customer_email:
        order_resp = await get_customer_latest_order(email=customer_email)
        internal["tool_traces"].append({
            "name": "get_customer_latest_order",
            "inputs": {"email": customer_email},
            "output": order_resp.model_dump(),
        })
        if order_resp.success and not order_resp.data.get("no_orders"):
            order_gid = order_resp.data.get("order_gid", "")
            if order_gid:
                tag_resp = await add_order_tags(order_gid=order_gid, tags=["Positive Feedback"])
                internal["tool_traces"].append({
                    "name": "add_order_tags",
                    "inputs": {"order_gid": order_gid, "tags": ["Positive Feedback"]},
                    "output": tag_resp.model_dump(),
                })

    # Determine workflow step based on conversation
    latest = _latest_user_text(state).lower()
    if any(word in latest for word in ("yes", "sure", "okay", "ok", "go ahead", "please")):
        internal["decided_action"] = "send_review_link"
    elif any(word in latest for word in ("no", "not now", "busy", "don't have time")):
        internal["decided_action"] = "declined_review"
    else:
        internal["decided_action"] = "ask_for_review"

    return {"internal_data": internal, "workflow_step": "ready_to_respond"}


# ── Node 2 — generate response ─────────────────────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Compose a warm, enthusiastic reply using feedback_system_prompt."""
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    customer = state.get("customer_info") or {}
    first_name = customer.get("first_name", "")
    action = internal.get("decided_action", "ask_for_review")

    context_parts: List[str] = [
        "Customer first name: %s" % first_name if first_name else "",
        "Decided action: %s" % action,
    ]
    context = "\n".join(p for p in context_parts if p)
    user_msgs = [m["content"] for m in state.get("messages", []) if m.get("role") == "user"]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = feedback_system_prompt()
    user_prompt = (
        "CONTEXT:\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a warm, enthusiastic reply (2-4 sentences with emojis). "
        "Do NOT include a subject line."
    )

    try:
        client = get_async_openai_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
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
        assistant_text = _fallback_response(action, first_name)

    new_msg = Message(role="assistant", content=assistant_text)
    return {
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "responded",
    }


def _fallback_response(action: str, first_name: str) -> str:
    name = first_name or "there"
    if action == "send_review_link":
        return (
            "Awwww, thank you! ❤️\n\n"
            "Here's the link to the review page: https://trustpilot.com/evaluate/naturalpatch.com\n\n"
            "Thanks so much! 🙏\n\nCaz xx"
        )
    if action == "declined_review":
        return (
            "No worries at all! Thanks so much for letting us know how happy you are. "
            "That means the world to us! 🥰\n\nCaz xx"
        )
    # ask_for_review
    return (
        "Awww 🥰 %s,\n\n"
        "That is so amazing! 🙏 Thank you for that epic feedback!\n\n"
        "If it's okay with you, would you mind if I send you a feedback request "
        "so you can share your thoughts on NATPAT and our response overall?\n\n"
        "It's totally fine if you don't have the time, but I thought I'd ask "
        "before sending a feedback request email 😊\n\nCaz" % name
    )


# ── Graph builder ──────────────────────────────────────────────────


def build_feedback_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("check_and_tag", node_check_and_tag)
    graph.add_node("generate_response", node_generate_response)
    graph.set_entry_point("check_and_tag")
    graph.add_edge("check_and_tag", "generate_response")
    graph.add_edge("generate_response", END)
    return graph.compile()


# ── FeedbackAgent class ────────────────────────────────────────────


class FeedbackAgent(BaseAgent):
    """Specialist agent for Positive Feedback workflows."""

    def __init__(self) -> None:
        super().__init__(name="feedback")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_feedback_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "positive_feedback"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["FeedbackAgent", "build_feedback_graph"]
