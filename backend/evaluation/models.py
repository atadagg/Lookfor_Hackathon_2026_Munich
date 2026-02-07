"""Data models for the evaluation system.

- Ticket: one evaluation item (single message or multi-turn).
- RunResult: outcome of running one ticket through the chat API.
- EvalSummary: aggregate metrics over many RunResults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Ticket:
    """One ticket to evaluate: matches ChatRequest shape with optional ground truth."""

    conversation_id: str
    user_id: str
    channel: str = "email"
    customer_email: str = ""
    first_name: str = ""
    last_name: str = ""
    shopify_customer_id: str = ""
    # Single message for one-turn, or use messages for multi-turn (sent in order).
    message: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None  # [{"role": "user", "content": "..."}, ...]

    # Optional ground truth for accuracy metrics.
    expected_agent: Optional[str] = None
    expected_intent: Optional[str] = None

    # Optional label for reporting (e.g. scenario name).
    label: Optional[str] = None

    def to_chat_payload(self, message_text: str) -> Dict[str, Any]:
        """Build a single ChatRequest-shaped payload for POST /chat."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "customer_email": self.customer_email or "eval@test.com",
            "first_name": self.first_name or "Eval",
            "last_name": self.last_name or "User",
            "shopify_customer_id": self.shopify_customer_id or "eval-cust",
            "message": message_text,
        }

    def iter_messages(self):
        """Yield (message_text,) for each user message to send (in order)."""
        if self.messages:
            for m in self.messages:
                if isinstance(m, dict) and m.get("role") == "user":
                    yield (m.get("content") or "",)
        elif self.message is not None:
            yield (self.message,)


@dataclass
class RunResult:
    """Result of running one ticket (possibly multi-turn) through the chat API."""

    ticket: Ticket
    # After last turn: agent, intent, is_escalated, last_assistant_message.
    agent: str = ""
    intent: str = ""
    is_escalated: bool = False
    last_assistant_message: Optional[str] = None
    # Per-run metadata.
    turns: int = 0
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    # Raw state from last response (for debugging).
    state: Dict[str, Any] = field(default_factory=dict)

    @property
    def routing_correct(self) -> Optional[bool]:
        """True/False if expected_agent was set and we can compare; else None."""
        if self.ticket.expected_agent is None:
            return None
        return (self.agent or "").strip().lower() == (self.ticket.expected_agent or "").strip().lower()

    @property
    def intent_correct(self) -> Optional[bool]:
        """True/False if expected_intent was set; else None."""
        if self.ticket.expected_intent is None:
            return None
        return (self.intent or "").strip() == (self.ticket.expected_intent or "").strip()


@dataclass
class EvalSummary:
    """Aggregate metrics over a set of RunResults."""

    total: int = 0
    escalated: int = 0
    errors: int = 0
    routing_correct: int = 0
    routing_total: int = 0  # only tickets with expected_agent
    intent_correct: int = 0
    intent_total: int = 0
    by_agent: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # agent -> {count, escalated, ...}
    by_intent: Dict[str, int] = field(default_factory=dict)
    latency_ms: List[float] = field(default_factory=list)
    results: List[RunResult] = field(default_factory=list)

    @property
    def escalation_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.escalated / self.total

    @property
    def error_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.errors / self.total

    @property
    def routing_accuracy(self) -> Optional[float]:
        if self.routing_total == 0:
            return None
        return self.routing_correct / self.routing_total

    @property
    def intent_accuracy(self) -> Optional[float]:
        if self.intent_total == 0:
            return None
        return self.intent_correct / self.intent_total
