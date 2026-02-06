"""Persistence layer and LangGraph checkpointer wiring.

During the hackathon you can plug in a real database (Postgres, Redis,
Dynamo, etc.) or just use in-memory dicts.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Checkpointer:
    """Very small placeholder around whatever LangGraph uses for state storage."""

    def __init__(self) -> None:
        # For now keep everything in-memory
        self._store: Dict[str, Dict[str, Any]] = {}

    def save_state(self, conversation_id: str, state: Dict[str, Any]) -> None:
        self._store[conversation_id] = state

    def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(conversation_id)


__all__ = ["Checkpointer"]
