"""LangGraph state machine for the Wrong/Missing Item workflow.

Graph structure
--------------
    check_order ──┬── [escalated]           ──> END
                  ├── [awaiting_order_id]    ──> END
                  └──> decide_step ──┬── [escalated / awaiting] ──> END
                                      └──> generate_response ──> END

Nodes
-----
1. check_order       Call get_orders_and_details or get_order_by_id; store order in internal_data.
2. decide_step       Classify user intent (LLM); escalate reship, execute credit/refund, or ask what happened / offer resolution.
3. generate_response Compose natural reply with wrong_item_system_prompt.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from langgraph.graph import END, StateGraph

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message
from schemas.internal import EscalationSummary
from .prompts import wrong_item_classify_prompt, wrong_item_system_prompt
from .tools import (
    add_order_tags,
    create_store_credit,
    extract_order_id,
    get_order_by_id,
    get_orders_and_details,
    refund_order_cash,
)

TAG_STORE_CREDIT = "Wrong or Missing, Store Credit Issued"
TAG_CASH_REFUND = "Wrong or Missing, Cash Refund Issued"


def _fresh_internal(state: AgentState) -> Dict[str, Any]:
    internal: Dict[str, Any] = dict(state.get("internal_data") or {})
    internal.setdefault("tool_traces", [])
    return internal


def _latest_user_text(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# ── Node 1 — check order ──────────────────────────────────────────


async def node_check_order(state: AgentState) -> dict:
    """Fetch orders and latest order details; store in internal_data."""

    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    customer_email = customer.get("email")
    prev_step = state.get("workflow_step") or ""

    # Resuming after we asked for an order ID
    if prev_step == "awaiting_order_id":
        latest_text = _latest_user_text(state)
        extracted = extract_order_id(latest_text)
        if not extracted:
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
                        "I'm looping in Monica, our Head of CS, who will take it from here."
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
                    "I couldn't spot an order number. Could you share it? "
                    "It usually looks like #12345 or NP12345."
                ),
            )
            return {
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "awaiting_order_id",
            }

        resp = await get_order_by_id(order_id=extracted)
        internal["tool_traces"].append({
            "name": "get_order_by_id",
            "inputs": {"order_id": extracted},
            "output": resp.model_dump(),
        })
        if not resp.success:
            internal["escalation_summary"] = EscalationSummary(
                reason="order_lookup_failed",
                details={"error": resp.error or "unknown", "order_id": extracted},
            ).model_dump()
            new_msg = Message(
                role="assistant",
                content=(
                    "I wasn't able to pull up that order. I'm looping in Monica, "
                    "our Head of CS, who will take it from here."
                ),
            )
            return {
                "is_escalated": True,
                "escalated_at": datetime.now(timezone.utc),
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "escalated_tool_error",
            }
        data = resp.data
        internal["order_id"] = data.get("order_id")
        internal["order_gid"] = data.get("order_gid")
        internal["customer_gid"] = data.get("customer_gid")
        internal["line_items"] = data.get("line_items", [])
        return {"internal_data": internal, "workflow_step": "checked_order"}

    # No email → escalate
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

    # Normal lookup by email
    resp = await get_orders_and_details(email=customer_email)
    internal["tool_traces"].append({
        "name": "get_orders_and_details",
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
        internal["_order_id_ask_count"] = 1
        new_msg = Message(
            role="assistant",
            content=(
                "I couldn't find any recent orders under your account. "
                "Could you share your order number? It usually looks like #12345 or NP12345."
            ),
        )
        return {
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "awaiting_order_id",
        }

    data = resp.data
    internal["order_id"] = data.get("order_id")
    internal["order_gid"] = data.get("order_gid")
    internal["customer_gid"] = data.get("customer_gid")
    internal["line_items"] = data.get("line_items", [])
    return {"internal_data": internal, "workflow_step": "checked_order"}


# ── Node 2 — decide step (classify + escalate / ask / offer / execute) ─


async def _classify_intent(latest_message: str) -> Dict[str, Any]:
    """Call LLM to extract issue_type and resolution preferences; return dict."""
    out = {
        "issue_type": None,
        "wants_reship": False,
        "wants_store_credit": False,
        "wants_refund": False,
    }
    if not latest_message or not latest_message.strip():
        return out
    try:
        client = get_async_openai_client()
        prompt = wrong_item_classify_prompt(latest_message)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (resp.choices[0].message.content or "").strip()
        # Extract JSON object (from first { to last })
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        obj = json.loads(text)
        out["issue_type"] = obj.get("issue_type") if obj.get("issue_type") in ("missing", "wrong", "unknown") else None
        out["wants_reship"] = bool(obj.get("wants_reship"))
        out["wants_store_credit"] = bool(obj.get("wants_store_credit"))
        out["wants_refund"] = bool(obj.get("wants_refund"))
    except Exception:
        pass
    return out


async def _validate_photos(photo_urls: List[str]) -> Tuple[bool, Optional[str]]:
    """Use vision API to check if photos show valid product/order content.
    Returns (is_valid, rejection_reason). rejection_reason is set when invalid.
    """
    if not photo_urls:
        return True, None
    try:
        client = get_async_openai_client()
        content: List[dict] = [
            {
                "type": "text",
                "text": (
                    "Does this image show a VALID photo for a wrong/missing item support ticket? "
                    "Valid = actual product items, parcel/box contents, packing slip, shipping label, "
                    "or anything a customer would send to prove what they received.\n"
                    "INVALID = memes, jokes, cartoons, screenshots of text only, unrelated images, "
                    "obvious pranks, or anything that is NOT a real photo of a product/parcel.\n"
                    "Reply with ONLY a JSON object: {\"valid\": true} or {\"valid\": false, \"reason\": \"brief explanation\"}"
                ),
            },
        ]
        for url in photo_urls[:3]:  # limit to first 3 to save tokens
            content.append({"type": "image_url", "image_url": {"url": url, "detail": "low"}})
        resp = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            max_tokens=128,
            messages=[{"role": "user", "content": content}],
        )
        text = (resp.choices[0].message.content or "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return True, None  # On parse failure, assume valid to avoid blocking
        obj = json.loads(text[start : end + 1])
        if obj.get("valid") is True:
            return True, None
        return False, obj.get("reason") or "Image does not appear to show product/parcel content."
    except Exception:
        return True, None  # On error, assume valid to avoid blocking real customers


async def node_decide_step(state: AgentState) -> dict:
    """Classify user intent; escalate reship, execute credit/refund, or ask / offer resolution."""

    internal = _fresh_internal(state)
    if state.get("is_escalated"):
        return {"workflow_step": "already_escalated"}

    latest = _latest_user_text(state)
    
    # Validate and track photos
    photo_urls = state.get("photo_urls", [])
    if photo_urls:
        is_valid, reject_reason = await _validate_photos(photo_urls)
        if not is_valid:
            internal["photos_received"] = False
            internal["photos_invalid"] = True
            new_msg = Message(
                role="assistant",
                content=(
                    "I'm sorry, I can't recognize the image—it doesn't seem to show "
                    "a photo of the product or parcel. Could you please send a clear "
                    "photo of what you received (the items, packing slip, or shipping label)?"
                ),
            )
            return {
                "internal_data": internal,
                "messages": list(state.get("messages", [])) + [new_msg],
                "workflow_step": "awaiting_valid_photo",
            }
        internal["photos_received"] = True
        internal["photo_urls"] = photo_urls
    
    # Run classification and persist
    if "issue_type" not in internal or internal.get("_classify_done") is not True:
        classified = await _classify_intent(latest)
        internal["issue_type"] = classified.get("issue_type")
        internal["wants_reship"] = classified.get("wants_reship", False)
        internal["wants_store_credit"] = classified.get("wants_store_credit", False)
        internal["wants_refund"] = classified.get("wants_refund", False)
        internal["_classify_done"] = True

    wants_reship = internal.get("wants_reship", False)
    wants_store_credit = internal.get("wants_store_credit", False)
    wants_refund = internal.get("wants_refund", False)
    issue_type = internal.get("issue_type")
    order_gid = internal.get("order_gid") or ""
    customer_gid = internal.get("customer_gid") or ""

    # Reship → escalate (ROADMAP: reship must trigger escalation)
    if wants_reship:
        internal["decided_action"] = "escalated_reship"
        new_msg = Message(
            role="assistant",
            content=(
                "Thanks for letting me know. I'm looping in Monica, our Head of CS, "
                "who will take it from here and process a free resend for you."
            ),
        )
        return {
            "is_escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "escalated_reship",
        }

    # Store credit: execute then go to generate_response
    if wants_store_credit and order_gid and customer_gid:
        amount = "10.00"  # Could be derived from order total later
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
            tag_resp = await add_order_tags(order_gid=order_gid, tags=[TAG_STORE_CREDIT])
            internal["tool_traces"].append({
                "name": "add_order_tags",
                "inputs": {"order_gid": order_gid, "tags": [TAG_STORE_CREDIT]},
                "output": tag_resp.model_dump(),
            })
        internal["decided_action"] = "confirmed_store_credit"
        internal["store_credit_amount"] = amount
        return {"internal_data": internal, "workflow_step": "execute_done"}

    # Cash refund: execute then go to generate_response
    if wants_refund and order_gid:
        refund_resp = await refund_order_cash(order_gid=order_gid)
        internal["tool_traces"].append({
            "name": "refund_order_cash",
            "inputs": {"order_gid": order_gid},
            "output": refund_resp.model_dump(),
        })
        if refund_resp.success:
            tag_resp = await add_order_tags(order_gid=order_gid, tags=[TAG_CASH_REFUND])
            internal["tool_traces"].append({
                "name": "add_order_tags",
                "inputs": {"order_gid": order_gid, "tags": [TAG_CASH_REFUND]},
                "output": tag_resp.model_dump(),
            })
        internal["decided_action"] = "confirmed_refund"
        return {"internal_data": internal, "workflow_step": "execute_done"}

    # No resolution choice yet: if we have issue_type, offer resolution; else ask what happened + photos
    if issue_type and issue_type != "unknown":
        # Thank customer if they provided photos
        photos_received = internal.get("photos_received", False)
        photo_thank = " Thanks for sharing the photo—that helps a lot!" if photos_received else ""
        
        new_msg = Message(
            role="assistant",
            content=(
                f"I'm sorry to hear that.{photo_thank} We can fix this in a few ways: "
                "I can arrange a free resend of the correct item, or offer you store credit "
                "(item value + 10% bonus), or process a refund to your original payment method. "
                "Which do you prefer?"
            ),
        )
        internal["decided_action"] = "offer_resolution"
        return {
            "internal_data": internal,
            "messages": list(state.get("messages", [])) + [new_msg],
            "workflow_step": "offered_resolution",
        }

    # Ask what happened + photos (Steps 2–3)
    new_msg = Message(
        role="assistant",
        content=(
            "I'm sorry to hear that! To get this sorted fast, could you tell me "
            "whether something is missing or you received the wrong item? "
            "If you can, send a photo of what you received—that really helps."
        ),
    )
    internal["decided_action"] = "ask_what_happened_and_photos"
    return {
        "internal_data": internal,
        "messages": list(state.get("messages", [])) + [new_msg],
        "workflow_step": "awaiting_what_happened",
    }


# ── Node 3 — generate response (LLM) ───────────────────────────────


async def node_generate_response(state: AgentState) -> dict:
    """Compose a natural reply using wrong_item_system_prompt and context."""

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
    if action == "confirmed_store_credit":
        context_parts.append("Store credit amount: %s" % internal.get("store_credit_amount", ""))
    
    # Add photo context if provided
    if internal.get("photos_received"):
        photo_urls = internal.get("photo_urls", [])
        context_parts.append(f"Photos received: {len(photo_urls)} photo(s) from customer")
    
    context = "\n".join(p for p in context_parts if p)
    user_msgs = [m["content"] for m in state.get("messages", []) if m.get("role") == "user"]
    latest_user = user_msgs[-1] if user_msgs else ""

    system_prompt = wrong_item_system_prompt()
    user_prompt = (
        "CONTEXT (from workflow):\n"
        + context
        + "\n\nCustomer's latest message:\n"
        + latest_user
        + "\n\nWrite a concise, friendly reply (2-3 sentences). "
        "Follow the wrong-item workflow rules. Do NOT invent information. Do NOT include a subject line."
    )

    try:
        client = get_async_openai_client()
        
        # Text-only prompt (we store photos for display but don't analyze them)
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
    if action == "ask_what_happened_and_photos":
        return (
            "I'm sorry to hear that. Could you tell me whether something is missing "
            "or you received the wrong item? A photo of what you received would help."
        )
    if action == "offer_resolution":
        return (
            "We can fix this with a free resend, store credit (item value + 10% bonus), "
            "or a refund. Which do you prefer?"
        )
    if action == "confirmed_store_credit":
        return "I've issued the store credit; it's available at checkout."
    if action == "confirmed_refund":
        return "I've processed the refund; it should appear in a few business days."
    return "%s: I'm sorry about the mix-up. How would you like to proceed?" % prefix


# ── Conditional routing ────────────────────────────────────────────


def _after_check_order(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") == "awaiting_order_id":
        return END
    return "decide_step"


def _after_decide_step(state: AgentState) -> str:
    if state.get("is_escalated"):
        return END
    if state.get("workflow_step") in ("awaiting_what_happened", "offered_resolution"):
        return END
    if state.get("workflow_step") == "execute_done":
        return "generate_response"
    return END


# ── Graph builder ──────────────────────────────────────────────────


def build_wrong_item_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("check_order", node_check_order)
    graph.add_node("decide_step", node_decide_step)
    graph.add_node("generate_response", node_generate_response)
    graph.set_entry_point("check_order")
    graph.add_conditional_edges("check_order", _after_check_order)
    graph.add_conditional_edges("decide_step", _after_decide_step)
    graph.add_edge("generate_response", END)
    return graph.compile()


# ── WrongItemAgent class ───────────────────────────────────────────


class WrongItemAgent(BaseAgent):
    """Specialist agent for Wrong/Missing Item workflows."""

    def __init__(self) -> None:
        super().__init__(name="wrong_item")
        self._app: Optional[Any] = None

    def build_graph(self) -> Any:
        if self._app is None:
            self._app = build_wrong_item_graph()
        return self._app

    async def handle(self, state: AgentState) -> AgentState:
        state["current_workflow"] = "wrong_item"
        app = self.build_graph()
        if hasattr(app, "ainvoke"):
            return await app.ainvoke(state)
        return app.invoke(state)


__all__ = ["WrongItemAgent", "build_wrong_item_graph"]
