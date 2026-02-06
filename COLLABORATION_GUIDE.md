# Multi-Agent Collaboration Guide

## Understanding Your Current System

Your system is **router-based**: 
- Router decides which agent handles the conversation
- One agent handles everything for that conversation
- Agents don't talk to each other

**This is perfectly valid!** Many production systems work this way.

## What Collaboration Means

Collaboration = Agents working together on the same problem.

### Example Scenario

**Customer says:** "My order is 2 weeks late AND I want a refund"

**Without collaboration (current):**
```
Router → Routes to WismoAgent (shipping delay)
WismoAgent → Handles shipping delay, ignores refund request
Customer → Frustrated, has to ask again
Router → Routes to RefundAgent (separate conversation)
```

**With collaboration:**
```
Router → Routes to WismoAgent (shipping delay)
WismoAgent → Sees customer also wants refund
WismoAgent → Consults RefundAgent: "Is this customer eligible for refund?"
RefundAgent → "Yes, based on delay policy"
WismoAgent → Handles BOTH: "Sorry for delay. I've processed your refund."
```

## Do You Need It?

**Probably not required for the hackathon**, but it's a nice-to-have that shows:
- Advanced system design
- Understanding of multi-agent concepts
- Better customer experience (handles complex requests)

## How to Add Collaboration (Simple Pattern)

### Option 1: Add to ConversationalAgent (Easier)

Agents like `RefundAgent`, `SubscriptionAgent` can easily add a `consult_agent` tool:

```python
# In RefundAgent or SubscriptionAgent
from core.agent_collaboration import consult_agent, CONSULT_AGENT_SCHEMA

class RefundAgent(ConversationalAgent):
    def __init__(self):
        super().__init__(name="refund")
        # Add consultation tool
        self._tool_schemas = [
            # ... existing tools ...
            CONSULT_AGENT_SCHEMA,  # <-- Add this
        ]
        self._tool_executors = {
            # ... existing executors ...
            "consult_agent": lambda agent_name, question, context, **kwargs: 
                consult_agent(agent_name, question, context, kwargs.get("state")),
        }
        # Update system prompt to mention collaboration
        self._system_prompt = """
        ... existing prompt ...
        
        If the customer mentions multiple issues (e.g., shipping delay + refund),
        you can consult other agents using consult_agent tool.
        """
```

**How it works:**
- LLM sees `consult_agent` in available tools
- LLM decides: "Customer wants refund AND order is delayed, let me consult WismoAgent"
- Calls `consult_agent("wismo", "Is this order delayed?", {...})`
- Gets response, incorporates into final answer

### Option 2: Add to Graph-Based Agents (WISMO)

For graph-based agents like WISMO, add a consultation node:

```python
async def node_check_for_cross_workflow_needs(state: AgentState) -> dict:
    """Check if customer mentioned other workflows that need collaboration."""
    
    latest_user = _latest_user_text(state)
    
    # Simple keyword detection (or use LLM)
    if "refund" in latest_user.lower() or "money back" in latest_user.lower():
        # Consult refund agent
        from core.agent_collaboration import consult_agent
        
        consultation = await consult_agent(
            agent_name="refund",
            question="Is this customer eligible for refund based on shipping delay?",
            context={
                "order_id": state.get("internal_data", {}).get("order_id"),
                "order_status": state.get("internal_data", {}).get("order_status"),
                "customer_request": latest_user,
            },
            current_state=state,
        )
        
        if consultation.get("success"):
            # Store consultation result
            internal = _fresh_internal(state)
            internal["refund_consultation"] = consultation
            return {"internal_data": internal}
    
    return {}
```

## Real-World Example

**Customer:** "My subscription charged me twice this month AND I want to cancel"

**With collaboration:**
1. Router → SubscriptionAgent
2. SubscriptionAgent detects: billing issue + cancellation request
3. SubscriptionAgent handles billing (fix double charge)
4. SubscriptionAgent handles cancellation
5. **Single response:** "I've fixed the double charge and cancelled your subscription"

**Without collaboration:**
1. Router → SubscriptionAgent (handles billing)
2. Customer has to ask again about cancellation
3. Router → SubscriptionAgent again (handles cancellation)
4. **Two separate interactions**

## Should You Implement This?

**For the hackathon:**
- ✅ **Nice to have** - Shows advanced understanding
- ❌ **Not required** - Your current system likely meets requirements
- ✅ **Easy to add** - Can be done in 1-2 hours

**Recommendation:** 
- If you have time: Add it to 1-2 agents as a demo
- If you're short on time: Focus on making your current system rock-solid

## Testing Collaboration

Test with complex requests:
- "My order is late AND I want a refund"
- "Cancel my subscription AND refund my last order"
- "Wrong item received AND I want store credit"

The agent should handle both parts in one response.
