"""Enhanced tool tracing with timing and observability metadata.

This module provides utilities for recording tool executions with
timestamps, durations, and metadata for observability.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from schemas.internal import ToolResponse

T = TypeVar("T")


class ToolTrace(Dict[str, Any]):
    """Enhanced tool trace with timing information."""

    def __init__(
        self,
        name: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        timestamp: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name=name,
            inputs=inputs,
            output=output,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            metadata=metadata or {},
        )


async def trace_async_tool_call(
    tool_name: str,
    tool_func: Callable[..., Awaitable[T]],
    **kwargs: Any,
) -> tuple[T, ToolTrace]:
    """Execute an async tool and return both result and trace with timing.

    Args:
        tool_name: Name of the tool for tracing
        tool_func: The async function to call
        **kwargs: Arguments to pass to tool_func

    Returns:
        Tuple of (result, trace_dict)

    Example:
        result, trace = await trace_async_tool_call(
            "get_order_status",
            get_order_status,
            email="customer@example.com"
        )
        internal["tool_traces"].append(trace)
    """
    start_time = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        result = await tool_func(**kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Handle both ToolResponse and dict outputs
        if hasattr(result, "model_dump"):
            output = result.model_dump()
        elif isinstance(result, dict):
            output = result
        else:
            output = {"result": str(result)}

        trace = ToolTrace(
            name=tool_name,
            inputs=kwargs,
            output=output,
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            metadata={
                "success": output.get("success", True) if isinstance(output, dict) else True,
                "has_error": "error" in output if isinstance(output, dict) else False,
            },
        )

        return result, trace

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000

        error_output = {
            "success": False,
            "error": f"Tool execution failed: {str(exc)}",
            "exception_type": type(exc).__name__,
        }

        trace = ToolTrace(
            name=tool_name,
            inputs=kwargs,
            output=error_output,
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            metadata={"success": False, "has_error": True, "exception": type(exc).__name__},
        )

        # Re-raise the exception after recording the trace
        raise


def trace_tool_call(
    tool_name: str,
    tool_func: Callable[..., T],
    **kwargs: Any,
) -> tuple[T, ToolTrace]:
    """Execute a sync tool and return both result and trace with timing.

    Args:
        tool_name: Name of the tool for tracing
        tool_func: The sync function to call
        **kwargs: Arguments to pass to tool_func

    Returns:
        Tuple of (result, trace_dict)

    Example:
        result, trace = trace_tool_call(
            "extract_order_id",
            extract_order_id,
            text="My order is #12345"
        )
        internal["tool_traces"].append(trace)
    """
    start_time = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        result = tool_func(**kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Handle both ToolResponse and dict outputs
        if hasattr(result, "model_dump"):
            output = result.model_dump()
        elif isinstance(result, dict):
            output = result
        else:
            output = {"result": str(result)}

        trace = ToolTrace(
            name=tool_name,
            inputs=kwargs,
            output=output,
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            metadata={
                "success": output.get("success", True) if isinstance(output, dict) else True,
                "has_error": "error" in output if isinstance(output, dict) else False,
            },
        )

        return result, trace

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000

        error_output = {
            "success": False,
            "error": f"Tool execution failed: {str(exc)}",
            "exception_type": type(exc).__name__,
        }

        trace = ToolTrace(
            name=tool_name,
            inputs=kwargs,
            output=error_output,
            timestamp=timestamp,
            duration_ms=round(duration_ms, 2),
            metadata={"success": False, "has_error": True, "exception": type(exc).__name__},
        )

        # Re-raise the exception after recording the trace
        raise


__all__ = ["ToolTrace", "trace_async_tool_call", "trace_tool_call"]
