# Observability & Tracing Guide

This guide explains how to use the enhanced observability features in the Fidelio multi-agent system.

## Overview

The observability system provides:

- **Tool Execution Tracing**: Automatic recording of all tool calls with inputs/outputs
- **Timing Metrics**: Precise timing data for each tool execution (milliseconds)
- **Performance Analytics**: Aggregated metrics across the entire conversation
- **Visual Timeline**: Frontend visualization showing execution flow and performance
- **Error Tracking**: Detailed error capture with exception types and messages
- **Multi-Agent Tracking**: Per-turn history showing agent handoffs and context switches

## Backend: Enhanced Tool Tracing

### Using the Tool Tracer

The `core.tool_tracer` module provides utilities to automatically capture timing and metadata:

```python
from core.tool_tracer import trace_async_tool_call, trace_tool_call

# For async tools
result, trace = await trace_async_tool_call(
    "get_order_status",
    get_order_status,
    email="customer@example.com"
)
internal["tool_traces"].append(trace)

# For sync tools
result, trace = trace_tool_call(
    "extract_order_id",
    extract_order_id,
    text="My order is #12345"
)
internal["tool_traces"].append(trace)
```

### Trace Data Structure

Each trace includes:

```python
{
    "name": "get_order_status",              # Tool name
    "inputs": {"email": "customer@..."},     # Input parameters
    "output": {                               # Tool response
        "success": True,
        "data": {...}
    },
    "timestamp": "2026-02-06T12:34:56.789Z", # ISO 8601 timestamp
    "duration_ms": 245.67,                    # Execution time in milliseconds
    "metadata": {                             # Additional metadata
        "success": True,
        "has_error": False
    }
}
```

### Migration Example

**Before (manual tracing):**

```python
async def node_check_order_status(state: AgentState) -> dict:
    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    
    tool_resp = await get_order_status(email=customer.get("email"))
    
    # Manual trace recording (no timing)
    internal["tool_traces"].append({
        "name": "get_order_status",
        "inputs": {"email": customer.get("email")},
        "output": tool_resp.model_dump(),
    })
    
    # ... rest of logic
```

**After (with enhanced tracing):**

```python
from core.tool_tracer import trace_async_tool_call

async def node_check_order_status(state: AgentState) -> dict:
    internal = _fresh_internal(state)
    customer = state.get("customer_info") or {}
    
    # Automatic timing and metadata capture
    tool_resp, trace = await trace_async_tool_call(
        "get_order_status",
        get_order_status,
        email=customer.get("email")
    )
    internal["tool_traces"].append(trace)
    
    # ... rest of logic (tool_resp is the same as before)
```

### Benefits

1. **Automatic Timing**: No need to manually calculate execution time
2. **Consistent Format**: All traces follow the same structure
3. **Error Handling**: Exceptions are caught and recorded with timing
4. **Zero Code Changes**: Result is identical to direct tool call
5. **Production Ready**: Minimal overhead (<1ms per trace)

## Frontend: Enhanced Trace Visualization

The trace tab now provides LangChain-style observability:

### 1. Execution Metrics Dashboard

High-level overview showing:
- Total tool calls with success rate
- Conversation turns
- Total messages exchanged
- Current status (Active/Escalated)
- Agents involved

### 2. Performance Timeline

Visual bar chart showing:
- Tool execution duration (ms/s)
- Relative performance comparison
- Success/failure status
- Agent attribution

### 3. Execution Flow Graph

Step-by-step visualization with:
- Intent classification
- Agent routing
- Tool calls with status
- Workflow decisions
- Final response/escalation

### 4. Detailed Tool Traces

Expandable cards for each tool call:
- Input parameters (JSON)
- Output response (JSON)
- Execution timestamp
- Duration metrics
- Error details (if any)

### 5. Session State Overview

Complete state inspection:
- Intent & routing info
- Customer information
- Agent decisions
- Extracted slots
- Escalation details

## Real Data vs Mock Data

All observability features use **real data** from the backend:

- **Tool Traces**: Captured from actual tool executions during the conversation
- **Timing Metrics**: Measured server-side using `time.perf_counter()`
- **Agent Turns**: Recorded from the LangGraph checkpoint state
- **Customer Info**: From the actual conversation context
- **Workflow Steps**: From the agent's state machine transitions

**No mock data** is used in the observability UI. If you don't see timing information:
1. Update agents to use `trace_async_tool_call` / `trace_tool_call`
2. Ensure backend is running with the latest code
3. Check that `internal_data.tool_traces` includes `duration_ms` fields

## Performance Impact

The tracing system has minimal overhead:

- **Per-trace overhead**: < 1ms (just timing calls)
- **Memory overhead**: ~500 bytes per trace (JSON storage)
- **Network overhead**: None (traces sent with existing state response)

For a typical conversation with 5-10 tool calls, the total overhead is < 10ms.

## Best Practices

### 1. Use Tracer for All Tools

Always wrap tool calls with the tracer:

```python
# ✅ Good
result, trace = await trace_async_tool_call("tool_name", tool_func, **kwargs)
internal["tool_traces"].append(trace)

# ❌ Bad (no timing)
result = await tool_func(**kwargs)
internal["tool_traces"].append({"name": "tool_name", "inputs": kwargs, "output": result.model_dump()})
```

### 2. Meaningful Tool Names

Use descriptive names that appear well in the UI:

```python
# ✅ Good
trace_async_tool_call("shopify_get_order_details", ...)
trace_async_tool_call("skio_cancel_subscription", ...)

# ❌ Bad
trace_async_tool_call("tool1", ...)
trace_async_tool_call("api_call", ...)
```

### 3. Include Context in Traces

The tracer automatically captures all kwargs:

```python
# ✅ Good - clear what was queried
await trace_async_tool_call(
    "get_order_details",
    get_order_details,
    order_id="#12345"
)

# ❌ Bad - context is lost
order_id = "#12345"
result = await get_order_details(order_id)
# Manual trace without proper inputs
```

### 4. Check for Errors

Tool traces capture errors automatically:

```python
try:
    result, trace = await trace_async_tool_call("tool", tool_func, **kwargs)
    internal["tool_traces"].append(trace)
    
    if not result.success:
        # Handle tool-level error (API returned error)
        logger.warning(f"Tool failed: {result.error}")
        
except Exception as exc:
    # Exception was already traced, but you can handle it
    logger.error(f"Tool crashed: {exc}")
    raise
```

## API Reference

### `trace_async_tool_call(tool_name, tool_func, **kwargs)`

Execute an async tool with automatic tracing.

**Parameters:**
- `tool_name` (str): Name of the tool for display
- `tool_func` (Callable): Async function to execute
- `**kwargs`: Arguments to pass to tool_func

**Returns:**
- `tuple[T, ToolTrace]`: (result, trace_dict)

**Raises:**
- Original exception from tool_func (after recording trace)

### `trace_tool_call(tool_name, tool_func, **kwargs)`

Execute a sync tool with automatic tracing.

**Parameters:**
- `tool_name` (str): Name of the tool for display
- `tool_func` (Callable): Sync function to execute
- `**kwargs`: Arguments to pass to tool_func

**Returns:**
- `tuple[T, ToolTrace]`: (result, trace_dict)

**Raises:**
- Original exception from tool_func (after recording trace)

### `ToolTrace` (class)

Enhanced trace dictionary with timing information.

**Fields:**
- `name` (str): Tool name
- `inputs` (dict): Input parameters
- `output` (dict): Tool response
- `timestamp` (str): ISO 8601 timestamp
- `duration_ms` (float): Execution time in milliseconds
- `metadata` (dict): Additional metadata

## Troubleshooting

### Traces appear but no timing data

**Cause**: Old trace format without `duration_ms`

**Fix**: Update agent code to use `trace_async_tool_call`:

```python
# Replace this:
internal["tool_traces"].append({
    "name": "tool",
    "inputs": {...},
    "output": {...}
})

# With this:
result, trace = await trace_async_tool_call("tool", tool_func, **kwargs)
internal["tool_traces"].append(trace)
```

### Performance timeline shows nothing

**Cause**: No traces have `duration_ms > 0`

**Fix**: Ensure you're using the tracer utilities, not manual trace creation.

### Timestamps are incorrect

**Cause**: Server timezone misconfiguration

**Fix**: The tracer uses `datetime.now(timezone.utc)` for consistency. Check system time.

## Examples

See these agents for reference implementations:

- `agents/wismo/graph.py` - Multi-step workflow with multiple tool calls
- `agents/wrong_item/graph.py` - Photo upload with MinIO integration
- `agents/refund/graph.py` - Complex decision tree with conditional tools

## Future Enhancements

Planned observability features:

- [ ] LLM token usage tracking
- [ ] Database query performance
- [ ] API endpoint latency distribution
- [ ] Error rate alerts
- [ ] Real-time trace streaming (WebSocket)
- [ ] Trace export (JSON/CSV)
- [ ] Performance regression detection
