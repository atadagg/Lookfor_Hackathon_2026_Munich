"""FastAPI server exposing the chat endpoint."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from core.state import AgentState, Message
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


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Initialize the shared state object
    state = AgentState(
        conversation_id=req.conversation_id,
        user_id=req.user_id,
        channel=req.channel,
        messages=[Message(role="user", content=req.message)],
    )

    # 1. Route to the right specialist
    state = await route(state)

    # 2. Dispatch to the specialist agent
    agents = get_agent_registry()
    agent = agents.get(state.routed_agent or "")
    if agent is None:
        # Fallback: echo state without modification
        return ChatResponse(
            conversation_id=state.conversation_id,
            agent=state.routed_agent or "unknown",
            state={"error": "No agent registered", "slots": state.slots},
        )

    state = await agent.handle(state)

    return ChatResponse(
        conversation_id=state.conversation_id,
        agent=agent.name,
        state={"intent": state.intent, "routed_agent": state.routed_agent, "slots": state.slots},
    )
