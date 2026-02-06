"""Prompts for WISMO shipping delay flows.

This module re-exports the prompt from the shipping sub-package for
backward compatibility.  All prompt logic lives in
``agents.shipping.prompts``.
"""

from __future__ import annotations

from agents.shipping.prompts import shipping_system_prompt


def wismo_system_prompt() -> str:
    """Return the system prompt for the WISMO / Shipping agent."""
    return shipping_system_prompt()


__all__ = ["wismo_system_prompt"]
