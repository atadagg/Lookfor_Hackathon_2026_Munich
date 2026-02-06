"""Simple agent-as-tool pattern.

One tool: call_agent(agent_name, customer_message)
- Runs the agent with the message
- Returns what that agent would say/do
- Calling agent incorporates into its response

That's it. Stupidly simple.
"""

from __future__ import annotations

from typing import Any, Dict

from core.state import AgentState
from main import get_agent_registry


async def call_agent(
    agent_name: str,
    customer_message: str,
    current_state: AgentState,
) -> Dict[str, Any]:
    """Call another agent as a tool.
    
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
        current_state: Current conversation state
    
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
    
    # Create a temporary state for the agent call
    # We're asking "what would you do?" not handling the real conversation
    temp_state: AgentState = {
        "conversation_id": current_state.get("conversation_id", "agent_call"),
        "user_id": current_state.get("user_id", ""),
        "channel": "internal_agent_call",
        "customer_info": current_state.get("customer_info", {}),
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


# Tool schema for LLM function calling
CALL_AGENT_SCHEMA = {
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


__all__ = ["call_agent", "CALL_AGENT_SCHEMA"]
