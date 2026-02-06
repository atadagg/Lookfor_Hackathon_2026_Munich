"""Shared OpenAI async client used by the router and all agents.

Lazily initialised so the module can be imported before ``load_dotenv``
has been called (the FastAPI server calls it at startup).
"""

from __future__ import annotations

import os
from typing import Optional

import openai

try:  # Optional – LangSmith is not required for local dev
    from langsmith.wrappers import wrap_openai
except Exception:  # pragma: no cover - best effort import
    wrap_openai = None  # type: ignore[assignment]


_async_client: Optional[openai.AsyncOpenAI] = None


def _build_client() -> openai.AsyncOpenAI:
    """Create an ``AsyncOpenAI`` client, optionally wrapped for LangSmith."""

    api_key = os.getenv("OPENAI_API_KEY") or getattr(openai, "api_key", None)
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set.  "
            "Add it to your .env file in the project root."
        )

    client: openai.AsyncOpenAI = openai.AsyncOpenAI(api_key=api_key)

    # Allow using LANGSMITH_* env vars (your current .env) while still
    # satisfying LangSmith's LANGCHAIN_* expectations.
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        if "LANGSMITH_API_KEY" in os.environ and "LANGCHAIN_API_KEY" not in os.environ:
            os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]
        if "LANGSMITH_ENDPOINT" in os.environ and "LANGCHAIN_ENDPOINT" not in os.environ:
            os.environ["LANGCHAIN_ENDPOINT"] = os.environ["LANGSMITH_ENDPOINT"]
        if "LANGSMITH_PROJECT" in os.environ and "LANGCHAIN_PROJECT" not in os.environ:
            # Remove quotes if someone set LANGSMITH_PROJECT="hackathon"
            proj = os.environ["LANGSMITH_PROJECT"].strip().strip('"').strip("'")
            os.environ["LANGCHAIN_PROJECT"] = proj

    # If LangSmith is installed and tracing is enabled, wrap the client so
    # all LLM calls show up in LangSmith without changing call sites.
    if wrap_openai is not None and os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
        client = wrap_openai(client)

    return client


def get_async_openai_client() -> openai.AsyncOpenAI:
    """Return a shared ``AsyncOpenAI`` client, creating it on first use."""

    global _async_client
    if _async_client is None:
        _async_client = _build_client()
    return _async_client


__all__ = ["get_async_openai_client"]
