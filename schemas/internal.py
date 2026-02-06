"""Internal shared schemas used across agents and tools.

This module defines a uniform `ToolResponse` contract so that every
Python tool adapter returns the same shape, matching the hackathon
specification:

- success: bool
- data: dict (optional structured payload)
- error: str (human-readable explanation when success is False)

It also contains a minimal `EscalationSummary` model used when an agent
escalates a conversation to a human.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """Uniform response model for all tool adapters.

    This matches the hackathon's API contract while staying Python-first,
    so agents and LLMs can reliably reason about tool outcomes.
    """

    success: bool = Field(..., description="Whether the tool call succeeded.")
    data: Any = Field(
        default_factory=dict,
        description="Structured payload returned by the tool on success (dict or list).",
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable explanation when success is False.",
    )


class EscalationSummary(BaseModel):
    """Structured payload attached to state when escalation is triggered."""

    reason: str = Field(..., description="Short machine-readable label.")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context: order id, status, message snippets, etc.",
    )


__all__ = ["ToolResponse", "EscalationSummary"]
