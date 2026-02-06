"""FastAPI server exposing the chat endpoint."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from core.state import AgentState, Message
from core.database import Checkpointer
from router.logic import route
from main import get_agent_registry


app = FastAPI(title="Lookfor Hackathon Support API")


class ChatRequest(BaseModel):
    conversation_id: str
    user_id: str
    channel: str = "web"
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    agent: str
    state: Dict[str, Any]


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

    # 1) Log inbound user message.
    checkpointer.save_message(
        req.conversation_id,
        role="user",
        content=req.message,
        direction="inbound",
    )

    # 2) Load previous state (if any) and extend the message history.
    prev_state = checkpointer.load_state(req.conversation_id) or {}

    # Lightweight filter: if this thread was already escalated, do not
    # re-enter the automated pipeline. Humans own it from here.
    if prev_state.get("is_escalated"):
        return ChatResponse(
            conversation_id=req.conversation_id,
            agent="escalated",
            state={"status": "escalated", "reason": "thread already escalated to human"},
        )

    messages = list(prev_state.get("messages", []))
    messages.append(Message(role="user", content=req.message))

    # Initialize / merge the shared state object.
    state = AgentState(
        **prev_state,
        conversation_id=req.conversation_id,
        user_id=req.user_id,
        channel=req.channel,
        messages=messages,
    )

    # 1. Route to the right specialist
    state = await route(state)

    # 2. Dispatch to the specialist agent
    agents = get_agent_registry()
    agent = agents.get(state.routed_agent or "")
    if agent is None:
        # Fallback: echo state without modification
        checkpointer.save_state(req.conversation_id, state)
        return ChatResponse(
            conversation_id=state.conversation_id,
            agent=state.routed_agent or "unknown",
            state={"error": "No agent registered", "slots": state.slots},
        )

    state = await agent.handle(state)

    # Persist the updated macro state so future turns can resume from it.
    checkpointer.save_state(req.conversation_id, state)

    # Log the latest assistant message (if any) for this turn.
    assistant_messages = [m for m in state.get("messages", []) if m.get("role") == "assistant"]
    if assistant_messages:
        last_assistant = assistant_messages[-1]
        checkpointer.save_message(
            req.conversation_id,
            role="assistant",
            content=last_assistant.get("content", ""),
            direction="outbound",
        )

    return ChatResponse(
        conversation_id=state.conversation_id,
        agent=agent.name,
        state={"intent": state.intent, "routed_agent": state.routed_agent, "slots": state.slots},
    )
