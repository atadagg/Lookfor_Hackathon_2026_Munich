"""LangGraph state machine for Discount / Promo Code workflow.

Graph structure
--------------
    check_code_created ──┬── [already_created] ──> generate_response ──> END
                          └── [not_created]     ──> create_code ──> generate_response ──> END

Nodes
-----
1. check_code_created  Look at internal_data to see if we already issued a code in this conversation.
2. create_code         Call create_discount_10_percent; store code in internal_data.
3. generate_response   Compose reply with discount_system_prompt.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from .prompts import discount_system_prompt
from .tools import create_discount_10_percent


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


# ── Node 1 — check if code already created ─────────────────────────


async def node_check_code_created(state: AgentState) -> dict:
    """Check if we already created a code in this conversation."""
    internal = _fresh_internal(state)
    if internal.get("discount_code"):
        return {"internal_data": internal, "workflow_step": "code_already_exists"}
    return {"internal_data": internal, "workflow_step": "need_to_create_code"}


# ── Node 2 — create discount code ──────────────────────────────────


async def node_create_code(state: AgentState) -> dict:
    """Create a 10% discount code valid for 48 hours."""
    internal = _fresh_internal(state)
    resp = await create_discount_10_percent(duration_hours=48)
    internal["tool_traces"].append({
        "name": "create_discount_10_percent",
        "inputs": {"duration_hours": 48},
        "output": resp.model_dump(),
    })
    if resp.success:
        code = resp.data.get("code", "")
        internal["discount_code"] = code
        internal["code_created"] = True
        internal["decided_action"] = "code_created"
    else:
        internal["decided_action"] = "code_creation_failed"
    return {"internal_data": internal, "workflow_step": "code_created"}


# ── Node 3 — generate response ─────────────────────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Compose a natural reply using discount_system_prompt and context."""
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    customer = state.get("customer_info") or {}
    first_name = customer.get("first_name", "")
    code = internal.get("discount_code", "")
    action = internal.get("decided_action", "")

    context_parts: List[str] = [
        "Customer first name: %s" % first_name if first_name else "",
        "Discount code: %s" % code if code else "No code created",
        "Decided action: %s" % action if action else "",
    ]
    context = "\n".join(p for p in context_parts if p)
    user_msgs = [m["content"] for m in state.get("messages", []) if m.get("role") == "user"]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = discount_system_prompt()
    user_prompt = (
        "CONTEXT:\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a concise, helpful reply (1-2 sentences). "
        "Include the discount code if we created one. Do NOT include a subject line."
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
        if code:
            assistant_text = (
                "Here's your 10%% discount code: %s. "
                "It's valid for 48 hours and single-use only. Enjoy!" % code
            )
        else:
            assistant_text = (
                "I'm sorry, I ran into an issue creating the code. "
                "Let me loop in support to help you out."
            )

    new_msg = Message(role="assistant", content=assistant_text)
    return {
        "messages": list(state.get("messages", [])) + [new_msg],
        "last_assistant_message": assistant_text,
        "workflow_step": "responded",
    }


# ── Conditional routing ────────────────────────────────────────────


def _after_check(state: AgentState) -> str:
    if state.get("workflow_step") == "code_already_exists":
        return "generate_response"
    return "create_code"


# ── Graph builder ──────────────────────────────────────────────────


def build_discount_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("check_code_created", node_check_code_created)
    graph.add_node("create_code", node_create_code)
    graph.add_node("generate_response", node_generate_response)
    graph.set_entry_point("check_code_created")
    graph.add_conditional_edges("check_code_created", _after_check)
    graph.add_edge("create_code", "generate_response")
    graph.add_edge("generate_response", END)
    return graph.compile()


# ── DiscountAgent class ────────────────────────────────────────────


class DiscountAgent(BaseAgent):
    """Specialist agent for Discount / Promo Code workflows."""

    def __init__(self) -> None:
        super().__init__(name="discount")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_discount_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "discount_code"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["DiscountAgent", "build_discount_graph"]
