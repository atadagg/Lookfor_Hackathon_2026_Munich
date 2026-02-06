"""Simple inter-agent collaboration mechanism.

This allows agents to consult other agents for decisions or information.
This is a simple pattern - agents can call other agents as "tools".
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.state import AgentState
from main import get_agent_registry


async def consult_agent(
    agent_name: str,
    question: str,
    context: Dict[str, Any],
    current_state: AgentState,
) -> Dict[str, Any]:
    """Allow one agent to consult another agent.
    
    This creates a sub-conversation with the consulted agent to get
    their expert opinion on a specific question.
    
    Args:
        agent_name: Name of the agent to consult (e.g., "refund")
        question: The question to ask the other agent
        context: Additional context to provide (e.g., order_id, customer_info)
        current_state: The current AgentState (for customer info, etc.)
    
    Returns:
        Dict with the consulted agent's response and recommendation
    """
    
    agents = get_agent_registry()
    target_agent = agents.get(agent_name)
    
    if not target_agent:
        return {
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }
    
    # Create a temporary state for the consultation
    # We're asking the agent a specific question, not handling a customer message
    consultation_state: AgentState = {
        "conversation_id": current_state.get("conversation_id", "consultation"),
        "user_id": current_state.get("user_id", ""),
        "channel": "internal_consultation",
        "customer_info": current_state.get("customer_info", {}),
        "messages": [
            {
                "role": "user",
                "content": (
                    f"CONSULTATION REQUEST:\n{question}\n\n"
                    f"CONTEXT: {context}\n\n"
                    "Please provide a brief expert opinion on this question. "
                    "You don't need to respond to a customer - just provide "
                    "your recommendation."
                ),
            }
        ],
        "internal_data": {},
    }
    
    try:
        # Run the agent (but it won't send a message to customer)
        result_state = await target_agent.handle(consultation_state)
        
        # Extract the agent's response
        messages = result_state.get("messages", [])
        agent_response = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                agent_response = msg.get("content", "")
                break
        
        if not agent_response:
            return {
                "success": False,
                "error": "Consulted agent did not provide a response",
            }
        
        return {
            "success": True,
            "agent": agent_name,
            "response": agent_response,
            "recommendation": agent_response,  # Could parse this more structured
            "internal_data": result_state.get("internal_data", {}),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Consultation failed: {str(exc)}",
        }


# Tool schema for LLM function calling
CONSULT_AGENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "consult_agent",
        "description": (
            "Consult another specialist agent for their expert opinion on a question. "
            "Use this when you need information or a decision from another agent's domain. "
            "For example, if handling a shipping delay but customer also wants a refund, "
            "consult the refund agent about eligibility."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent to consult: refund, subscription, order_mod, etc.",
                    "enum": ["refund", "subscription", "order_mod", "wismo", "wrong_item", "product_issue"],
                },
                "question": {
                    "type": "string",
                    "description": "The specific question or decision you need help with",
                },
                "context": {
                    "type": "object",
                    "description": "Relevant context (order_id, order_status, customer_request, etc.)",
                },
            },
            "required": ["agent_name", "question", "context"],
        },
    },
}


__all__ = ["consult_agent", "CONSULT_AGENT_SCHEMA"]
