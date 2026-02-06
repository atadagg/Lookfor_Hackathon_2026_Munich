"""Shared OpenAI async client used by the router and all agents.

Lazily initialised so the module can be imported before ``load_dotenv``
has been called (the FastAPI server calls it at startup).
"""

from __future__ import annotations

import os
from typing import Optional

import openai

_async_client: Optional[openai.AsyncOpenAI] = None


def get_async_openai_client() -> openai.AsyncOpenAI:
    """Return a shared ``AsyncOpenAI`` client, creating it on first use."""

    global _async_client
    if _async_client is None:
        api_key = os.getenv("OPENAI_API_KEY") or getattr(openai, "api_key", None)
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set.  "
                "Add it to your .env file in the project root."
            )
        _async_client = openai.AsyncOpenAI(api_key=api_key)
    return _async_client


__all__ = ["get_async_openai_client"]
