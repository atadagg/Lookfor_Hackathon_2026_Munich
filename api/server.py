"""FastAPI server exposing the chat endpoint."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import openai

from core.state import AgentState, Message
from core.database import Checkpointer
from router.logic import route
from main import get_agent_registry


app = FastAPI(title="Lookfor Hackathon Support API")

# Load environment and configure OpenAI at the boundary of the app.
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key


class ChatRequest(BaseModel):
    conversation_id: str
    user_id: str
    # Channel is kept generic; in the hackathon this will usually be "email".
    channel: str = "email"
    # Email session metadata provided at the start of the thread.
    customer_email: str
    first_name: str
    last_name: str
    shopify_customer_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    agent: str
    state: Dict[str, Any]


class ThreadSnapshot(BaseModel):
    conversation_id: str
    status: str
    current_workflow: Optional[str] = None
    workflow_step: Optional[str] = None
    is_escalated: bool
    escalated_at: Optional[str] = None
    messages: List[Dict[str, Any]]


# Single shared checkpointer instance.
checkpointer = Checkpointer()


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Main chat entrypoint.

    Steps:
    1. Log the inbound message to SQLite.
    2. Load any previous AgentState for this conversation.
    3. If the thread is already escalated, short-circuit and do not
       re-enter the automated pipeline.
    4. Otherwise, run router + specialist agent and persist the updated
       state + assistant reply.
    """

    # 1) Log inbound user message (with duplicate detection).
    was_new = checkpointer.save_message(
        req.conversation_id,
        role="user",
        content=req.message,
        direction="inbound",
    )

    if not was_new:
        # Exact same message already recorded -- warn and don't re-process.
        return ChatResponse(
            conversation_id=req.conversation_id,
            agent="duplicate",
            state={
                "warning": "Duplicate message detected -- identical to the last inbound message. Skipped.",
            },
        )

    # 2) Load previous state (if any) and extend the message history.
    prev_state = checkpointer.load_state(req.conversation_id) or {}

    # Lightweight filter: if this thread was already escalated, do not
    # re-enter the automated pipeline. Humans own it from here.
    if prev_state.get("is_escalated"):
        internal = (prev_state.get("internal_data") or {}) if isinstance(prev_state, dict) else {}
        escalation_summary = internal.get("escalation_summary")
        return ChatResponse(
            conversation_id=req.conversation_id,
            agent="escalated",
            state={
                "status": "escalated",
                "reason": "thread already escalated to human",
                "escalation_summary": escalation_summary,
            },
        )

    messages = list(prev_state.get("messages", []))
    messages.append(Message(role="user", content=req.message))

    # Merge / override customer info from the request.
    prev_customer = prev_state.get("customer_info", {}) if isinstance(prev_state, dict) else {}
    customer_info = {
        **prev_customer,
        "email": req.customer_email,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "shopify_customer_id": req.shopify_customer_id,
    }

    # Build the state from scratch, carrying over only the fields from
    # prev_state that we don't explicitly set (e.g. internal_data,
    # workflow_step, is_escalated, etc.).  This avoids "got multiple
    # values for keyword argument" errors on repeated calls.
    state: dict = dict(prev_state)  # shallow copy
    state.update(
        conversation_id=req.conversation_id,
        user_id=req.user_id,
        channel=req.channel,
        customer_info=customer_info,
        messages=messages,
    )

    # 1. Route to the right specialist
    state = await route(state)

    # If routing has already escalated the thread (e.g. LLM error), do
    # not invoke any specialist agents. Persist state and return the
    # escalated snapshot to the caller.
    if state.get("is_escalated"):
        checkpointer.save_state(req.conversation_id, state)

        assistant_messages = [m for m in state.get("messages", []) if m.get("role") == "assistant"]
        if assistant_messages:
            last_assistant = assistant_messages[-1]
            checkpointer.save_message(
                req.conversation_id,
                role="assistant",
                content=last_assistant.get("content", ""),
                direction="outbound",
            )

        internal = state.get("internal_data", {}) or {}
        tool_traces = internal.get("tool_traces") or []
        escalation_summary = internal.get("escalation_summary")

        last_assistant_message = last_assistant.get("content", "") if assistant_messages else None

        return ChatResponse(
            conversation_id=state.get("conversation_id", req.conversation_id),
            agent="escalated",
            state={
                "intent": state.get("intent"),
                "routed_agent": state.get("routed_agent"),
                "current_workflow": state.get("current_workflow"),
                "workflow_step": state.get("workflow_step"),
                "is_escalated": state.get("is_escalated", False),
                "escalation_summary": escalation_summary,
                "last_assistant_message": last_assistant_message,
                "internal_data": {
                    "tool_traces": tool_traces,
                },
            },
        )

    # 2. Dispatch to the specialist agent
    agents = get_agent_registry()
    routed_agent = state.get("routed_agent") or ""
    agent = agents.get(routed_agent)
    if agent is None:
        # Fallback: echo state without modification
        checkpointer.save_state(req.conversation_id, state)
        conv_id = state.get("conversation_id", req.conversation_id)
        return ChatResponse(
            conversation_id=conv_id,
            agent=routed_agent or "unknown",
            state={
                "error": "No agent registered",
                "intent": state.get("intent"),
                "routed_agent": state.get("routed_agent"),
            },
        )

    state = await agent.handle(state)

    # Persist the updated macro state so future turns can resume from it.
    checkpointer.save_state(req.conversation_id, state)

    # Log the latest assistant message (if any) for this turn.
    raw_messages = state.get("messages", []) or []
    assistant_text: Optional[str] = None

    for msg in reversed(raw_messages):
        # Messages may be plain dicts or LangChain-style objects.
        if isinstance(msg, dict):
            if msg.get("role") == "assistant":
                assistant_text = msg.get("content", "")
                break
        else:
            role = getattr(msg, "role", None) or getattr(msg, "type", None)
            if role == "assistant":
                assistant_text = getattr(msg, "content", None) or getattr(msg, "text", None)
                break

    if assistant_text:
        checkpointer.save_message(
            req.conversation_id,
            role="assistant",
            content=assistant_text,
            direction="outbound",
        )

    # Prepare observable state payload for the caller.
    internal = state.get("internal_data", {}) or {}
    tool_traces = internal.get("tool_traces") or []
    escalation_summary = internal.get("escalation_summary")

    last_assistant_message = assistant_text

    conv_id = state.get("conversation_id", req.conversation_id)

    return ChatResponse(
        conversation_id=conv_id,
        agent=agent.name,
        state={
            "intent": state.get("intent"),
            "routed_agent": state.get("routed_agent"),
            "current_workflow": state.get("current_workflow"),
            "workflow_step": state.get("workflow_step"),
            "is_escalated": state.get("is_escalated", False),
            "escalation_summary": escalation_summary,
            "last_assistant_message": last_assistant_message,
            "internal_data": {
                "tool_traces": tool_traces,
            },
        },
    )


@app.get("/thread/{conversation_id}", response_model=ThreadSnapshot)
async def get_thread(conversation_id: str) -> ThreadSnapshot:
    """Read-only endpoint to inspect a thread's status and messages."""

    thread = checkpointer.get_thread(conversation_id)
    messages = checkpointer.get_messages(conversation_id)

    if thread is None:
        # Return an empty shell so evaluators can still hit the endpoint safely.
        return ThreadSnapshot(
            conversation_id=conversation_id,
            status="not_found",
            current_workflow=None,
            workflow_step=None,
            is_escalated=False,
            escalated_at=None,
            messages=[],
        )

    return ThreadSnapshot(
        conversation_id=thread.external_thread_id,
        status=thread.status,
        current_workflow=thread.current_workflow,
        workflow_step=thread.workflow_step,
        is_escalated=thread.is_escalated,
        escalated_at=thread.escalated_at,
        messages=messages,
    )
