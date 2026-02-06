"""Global `AgentState` definition shared across router and all specialists.

Keep this minimal for now; you can expand it during the hackathon as
requirements become clearer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Top-level state that flows through the router and specialist graphs."""

    conversation_id: str
    messages: List[Message] = field(default_factory=list)

    # High-level routing info (set by router)
    intent: Optional[str] = None
    routed_agent: Optional[str] = None

    # Arbitrary scratchpad for graphs / tools
    slots: Dict[str, Any] = field(default_factory=dict)

    # Persistence / metadata hooks
    user_id: Optional[str] = None
    channel: Optional[str] = None  # e.g. "web", "sms", "email"


__all__ = ["Message", "AgentState"]
