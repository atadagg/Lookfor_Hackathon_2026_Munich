"""Typed AgentState definition shared across router and specialist agents.

This module defines the **macro state** that flows through LangGraph.
It is intentionally minimal and uses `TypedDict` + `Annotated` so it
plays nicely with LangGraph's `add_messages` helper.

The vertical slice in this hackathon focuses on the **shipping** /
WISMO workflow, but the same state container can be reused for other
specialists (refunds, subscriptions, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import add_messages
from typing_extensions import Annotated


class Message(TypedDict):
    """Single chat message exchanged in the session."""

    role: Literal["user", "assistant", "system"]
    content: str


class CustomerInfo(TypedDict, total=False):
    """Customer metadata provided at email session start."""

    email: str
    first_name: str
    last_name: str
    shopify_customer_id: str


class AgentState(TypedDict, total=False):
    """Top-level state that flows through router and specialist graphs.

    Fields are deliberately generic so the same container can represent
    any workflow (shipping, refund, subscription, etc.).
    """

    # Core identifiers for the thread / user / channel.
    conversation_id: str
    user_id: str
    channel: str

    # High-level routing metadata set by the receptionist.
    intent: str
    routed_agent: str

    # Optional per-agent scratchpad for slots / extracted fields.
    slots: Dict[str, Any]

    # Full conversation history for continuous memory.
    messages: Annotated[List[Message], add_messages]

    # Customer identity & Shopify linkage.
    customer_info: CustomerInfo

    # Name of the active workflow, e.g. "shipping".
    current_workflow: str

    # Fine-grained step label within the workflow, e.g. "checked_status",
    # "wait_promise_set", "escalated".
    workflow_step: str

    # Arbitrary scratchpad for tool outputs and intermediate data.
    # Example keys for shipping:
    # - "order_status"
    # - "tracking_url"
    # - "wait_promise_until" (ISO8601 date string)
    internal_data: Dict[str, Any]

    # Escalation flag + optional metadata.
    is_escalated: bool
    escalated_at: Optional[datetime]


__all__ = ["Message", "CustomerInfo", "AgentState"]

