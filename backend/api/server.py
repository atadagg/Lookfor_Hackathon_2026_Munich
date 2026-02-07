"""FastAPI server exposing the chat endpoint."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from core.state import AgentState, Message
from core.database import Checkpointer
from core.mas_behavior import (
    add_behavior_override,
    add_prompt_policy,
    get_full_config,
    remove_agent_prompt_policy_at,
    remove_behavior_override,
    remove_behavior_override_at,
    remove_prompt_policy_at,
)
from core.mas_interpret import interpret_nl_to_mas_update
from core.storage import get_attachment_stream, upload_attachment
from router.logic import route
from main import get_agent_registry
from utils.minio_client import upload_photo, download_photo
from api.playground import router as playground_router


app = FastAPI(title="Lookfor Hackathon Support API")

# Include playground routes
app.include_router(playground_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment at the boundary of the app.
load_dotenv()


# Cached agent registry — created once at module load, not per request.
_agent_registry = None


def _get_agents():
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = get_agent_registry()
    return _agent_registry


class MASUpdateRequest(BaseModel):
    """Update MAS behavior: add a prompt policy and/or a structured behavior override."""

    instruction: Optional[str] = None
    behavior_override: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck."""
    return {"status": "healthy", "service": "fidelio-backend"}


# ──────────────────────────────────────────────────────────────────────
# MAS behavior config (single file: config/mas_behavior.yaml)
# ──────────────────────────────────────────────────────────────────────


@app.get("/mas/behavior")
async def get_mas_behavior():
    """Return the current MAS behavior config (prompt_policies, behavior_overrides)."""
    return get_full_config()


@app.post("/mas/update")
async def post_mas_update(req: Dict[str, Any] = Body(default_factory=dict)):
    """Update MAS behavior: add or remove. Add: instruction, agent, behavior_override. Remove: remove_prompt_policy_index (int), remove_agent_policy {agent, index}, remove_behavior_override {agent, index? or trigger?}."""
    if not isinstance(req, dict):
        return get_full_config()
    # Add
    instruction = req.get("instruction")
    if instruction and isinstance(instruction, str):
        agent = req.get("agent")
        add_prompt_policy(instruction.strip(), agent=agent if isinstance(agent, str) else None)
    bo = req.get("behavior_override")
    if isinstance(bo, dict) and bo.get("agent"):
        add_behavior_override(bo["agent"], bo)
    # Remove
    idx = req.get("remove_prompt_policy_index")
    if isinstance(idx, int) and idx >= 0:
        remove_prompt_policy_at(idx)
    rap = req.get("remove_agent_policy")
    if isinstance(rap, dict) and isinstance(rap.get("agent"), str) and isinstance(rap.get("index"), int):
        remove_agent_prompt_policy_at(rap["agent"], rap["index"])
    rbo = req.get("remove_behavior_override")
    if isinstance(rbo, dict) and rbo.get("agent"):
        if isinstance(rbo.get("trigger"), str):
            remove_behavior_override(rbo["agent"], rbo["trigger"])
        elif isinstance(rbo.get("index"), int) and rbo["index"] >= 0:
            remove_behavior_override_at(rbo["agent"], rbo["index"])
    return get_full_config()


@app.post("/mas/interpret")
async def post_mas_interpret(req: Dict[str, Any] = Body(default_factory=dict)):
    """Interpret natural language into MAS updates and apply them. Body: {"prompt": "If a customer wants to update their order address, do not update it directly. Mark as NEEDS_ATTENTION and escalate."}. Returns config + applied summary + error if any."""
    if not isinstance(req, dict):
        return {"config": get_full_config(), "applied": {}, "error": "Body must be a JSON object"}
    prompt = req.get("prompt")
    if not prompt or not isinstance(prompt, str):
        return {"config": get_full_config(), "applied": {}, "error": "Missing or invalid 'prompt' string"}
    return await interpret_nl_to_mas_update(prompt)


class AttachmentInput(BaseModel):
    """Base64-encoded image attachment from email/webhook."""

    filename: Optional[str] = None
    content_type: str = "image/jpeg"
    data: str  # base64-encoded bytes


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
    # Photo URLs (MinIO URLs for UC2: Wrong Item, e.g. from hackathon platform)
    photo_urls: Optional[List[str]] = None
    # Base64-encoded image attachments (from email with images)
    attachments: Optional[List[AttachmentInput]] = None


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

    # 1) Process attachments: upload to MinIO (or local fallback) and collect refs
    # Also build data URLs for the AI (OpenAI vision API accepts data:image/...;base64,...)
    attachments_meta: List[Dict[str, Any]] = []
    photo_urls_for_ai: List[str] = []
    if req.attachments:
        for att in req.attachments:
            try:
                raw = base64.b64decode(att.data)
            except Exception:
                continue
            meta = upload_attachment(
                req.conversation_id,
                raw,
                att.content_type,
                att.filename,
            )
            if meta:
                attachments_meta.append(meta)
                # Data URLs work with OpenAI vision API (no public URL needed)
                if (att.content_type or "").startswith("image/"):
                    photo_urls_for_ai.append(f"data:{att.content_type};base64,{att.data}")
    attachments_json_str = json.dumps(attachments_meta) if attachments_meta else None

    # 2) Log inbound user message (with duplicate detection).
    was_new = checkpointer.save_message(
        req.conversation_id,
        role="user",
        content=req.message,
        direction="inbound",
        attachments_json=attachments_json_str,
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
    
    # Add photo URLs for the AI (UC2: Wrong Item) - from photo_urls and/or attachments
    all_photo_urls: List[str] = list(req.photo_urls or []) + photo_urls_for_ai
    if all_photo_urls:
        state["photo_urls"] = all_photo_urls

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

        last_assistant_message = assistant_messages[-1].get("content", "") if assistant_messages else None
        conv_id = state.get("conversation_id", req.conversation_id)

        return ChatResponse(
            conversation_id=conv_id,
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
    agents = _get_agents()
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

    try:
        state = await agent.handle(state)
    except Exception as exc:
        # Gracefully catch unhandled agent errors → escalate instead of 500
        internal = state.get("internal_data") or {}
        internal.setdefault("tool_traces", [])
        internal["escalation_summary"] = {
            "reason": "agent_error",
            "details": {"error": str(exc), "agent": routed_agent},
        }
        state["internal_data"] = internal
        state["is_escalated"] = True
        state["workflow_step"] = "escalated_agent_error"
        msgs = list(state.get("messages", []))
        msgs.append({
            "role": "assistant",
            "content": (
                "I ran into a technical issue processing your request. "
                "To make sure you get the right support, I'm looping in "
                "Monica, our Head of CS, who will take it from here."
            ),
        })
        state["messages"] = msgs

    # Append this turn to agent_turn_history so the UI can show which agent
    # handled each turn (e.g. wismo → refund) and preserve tool traces.
    internal = state.get("internal_data") or {}
    current_traces = list(internal.get("tool_traces") or [])
    turn_history: List[Dict[str, Any]] = list(state.get("agent_turn_history") or [])
    turn_history.append({
        "agent": agent.name,
        "intent": state.get("intent"),
        "current_workflow": state.get("current_workflow"),
        "workflow_step": state.get("workflow_step"),
        "tool_traces": current_traces,
    })
    state["agent_turn_history"] = turn_history

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

    # Pass through full internal_data so agents can expose order_id, order_gid, etc.
    internal_data_response = dict(internal)

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
            "agent_turn_history": state.get("agent_turn_history"),
            "internal_data": internal_data_response,
        },
    )


def _add_attachment_urls(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add 'url' to each attachment for frontend display."""
    out = []
    for msg in messages:
        m = dict(msg)
        atts = m.get("attachments") or []
        enriched = []
        for a in atts:
            obj_key = a.get("object_key")
            if obj_key:
                b64 = base64.urlsafe_b64encode(obj_key.encode("utf-8")).decode("ascii").rstrip("=")
                enriched.append({**a, "url": f"/attachment?key={b64}"})
            else:
                enriched.append(a)
        m["attachments"] = enriched
        out.append(m)
    return out


@app.get("/attachment")
async def get_attachment(key: str):
    """Stream an attachment by its base64-encoded object_key. Used by frontend to display images."""
    try:
        # Decode key (padding may have been stripped)
        pad = 4 - len(key) % 4
        if pad != 4:
            key += "=" * pad
        object_key = base64.urlsafe_b64decode(key).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid attachment key")
    result = get_attachment_stream(object_key)
    if result is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    data, content_type = result
    return Response(content=data, media_type=content_type)


@app.get("/thread/{conversation_id}", response_model=ThreadSnapshot)
async def get_thread(conversation_id: str) -> ThreadSnapshot:
    """Read-only endpoint to inspect a thread's status and messages."""

    thread = checkpointer.get_thread(conversation_id)
    messages = checkpointer.get_messages(conversation_id)
    messages = _add_attachment_urls(messages)

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


@app.get("/threads")
async def list_threads():
    """List all conversation threads for the sidebar."""
    return checkpointer.list_threads()


@app.get("/thread/{conversation_id}/state")
async def get_thread_state(conversation_id: str):
    """Return the full serialised AgentState for a thread."""
    state = checkpointer.load_state(conversation_id)
    if state is None:
        return {"error": "not_found"}
    return state


# ──────────────────────────────────────────────────────────────────────
# Photo Upload/Download Endpoints (UC2: Wrong Item)
# ──────────────────────────────────────────────────────────────────────


@app.post("/photos/upload")
async def upload_customer_photo(file: UploadFile = File(...)):
    """
    Upload a customer photo to MinIO storage.
    
    Used by the frontend when customers attach photos to their support messages
    (primarily for UC2: Wrong Item workflow).
    
    Returns:
        {
            "success": bool,
            "url": str (public MinIO URL for the uploaded photo),
            "filename": str,
            "message": str (optional)
        }
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only images are allowed.",
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content)} bytes. Maximum size is {max_size} bytes (10MB).",
        )
    
    # Upload to MinIO
    result = await upload_photo(content, file.filename or "photo.jpg")
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Upload failed"),
        )
    
    return result


@app.get("/photos/download")
async def download_customer_photo(url: str):
    """
    Download a photo from MinIO storage.
    
    Args:
        url: Full MinIO URL of the photo
    
    Returns:
        Binary image content with appropriate content-type header
    """
    result = await download_photo(url)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Photo not found"),
        )
    
    return Response(
        content=result["content"],
        media_type=result.get("content_type", "image/jpeg"),
    )
