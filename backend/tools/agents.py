"""Agent-as-tool adapter for inter-agent collaboration.

This tool allows agents to call other agents, enabling multi-agent collaboration.
When a customer mentions multiple issues, one agent can call another to handle
part of the request.

Pattern matches other tools:
- Executor function: call_agent()
- Schema: SCHEMA_CALL_AGENT
- Exported in EXECUTORS dict
"""

from __future__ import annotations

from typing import Any, Dict

from core.state import AgentState
from main import get_agent_registry


async def call_agent(
    agent_name: str,
    customer_message: str,
    state: AgentState | None = None,
) -> Dict[str, Any]:
    """Call another specialist agent as a tool.
    
    This runs the agent with the given message and returns what it would
    say/do. The calling agent can then incorporate this into its response.
    
    Example:
        WismoAgent handling "order late + refund"
        → calls call_agent("refund", "customer wants refund", state)
        → RefundAgent returns: "I'll process your refund"
        → WismoAgent combines: "Sorry for delay. I've processed your refund."
    
    Args:
        agent_name: Which agent to call (refund, subscription, etc.)
        customer_message: The message/question for that agent
        state: Current conversation state (passed by executor wrapper)
    
    Returns:
        {
            "success": bool,
            "response": "what the agent would say",
            "actions_taken": [...],  # tool traces from that agent
        }
    """
    
    agents = get_agent_registry()
    target_agent = agents.get(agent_name)
    
    if not target_agent:
        return {
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }
    
    if not state:
        return {
            "success": False,
            "error": "State not provided to call_agent",
        }
    
    # Create a temporary state for the agent call
    # We're asking "what would you do?" not handling the real conversation
    temp_state: AgentState = {
        "conversation_id": state.get("conversation_id", "agent_call"),
        "user_id": state.get("user_id", ""),
        "channel": "internal_agent_call",
        "customer_info": state.get("customer_info", {}),
        "messages": [
            {
                "role": "user",
                "content": customer_message,
            }
        ],
        "internal_data": {},
    }
    
    try:
        # Run the agent
        result_state = await target_agent.handle(temp_state)
        
        # Extract what the agent would say
        messages = result_state.get("messages", [])
        agent_response = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                agent_response = msg.get("content", "")
                break
        
        # Extract what actions it took (tool traces)
        tool_traces = result_state.get("internal_data", {}).get("tool_traces", [])
        
        return {
            "success": True,
            "agent": agent_name,
            "response": agent_response or "Agent processed the request",
            "actions_taken": tool_traces,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Agent call failed: {str(exc)}",
        }


SCHEMA_CALL_AGENT = {
    "type": "function",
    "function": {
        "name": "call_agent",
        "description": (
            "Call another specialist agent to handle part of the customer's request. "
            "Use this when the customer mentions multiple issues. "
            "Example: Customer says 'order late + refund' - you handle shipping, "
            "call refund agent for the refund part, then combine responses."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Which agent to call",
                    "enum": ["refund", "subscription", "order_mod", "wismo", "wrong_item", "product_issue", "discount"],
                },
                "customer_message": {
                    "type": "string",
                    "description": "The customer's message/question for that agent (e.g., 'customer wants refund')",
                },
            },
            "required": ["agent_name", "customer_message"],
        },
    },
}


EXECUTORS = {
    "call_agent": call_agent,
}


__all__ = ["call_agent", "SCHEMA_CALL_AGENT", "EXECUTORS"]
