"""Shared tools (Shopify, CRM, tagging, etc.).

Populate this package with real tool implementations as you integrate
external systems.
"""

from typing import Protocol, Any, Dict


class Tool(Protocol):
    """Very small protocol for tools that can be called by agents."""

    name: str

    async def __call__(self, **kwargs: Any) -> Dict[str, Any]:  # pragma: no cover - stub
        ...


__all__ = ["Tool"]
