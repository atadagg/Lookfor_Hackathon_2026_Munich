# Simple Multi-Agent Collaboration

## The Problem

Customer says: **"My order is late AND I want a refund"**

Current system:
- Router picks ONE agent (WismoAgent for shipping)
- WismoAgent handles shipping, ignores refund
- Customer frustrated

## The Solution

**One tool: `call_agent(agent_name, customer_message)`**

That's it. Stupidly simple.

## How It Works

```
Customer: "Order late + refund"

1. Router → WismoAgent (handles shipping)
2. WismoAgent detects: "Customer also wants refund"
3. WismoAgent calls: call_agent("refund", "customer wants refund")
4. RefundAgent runs, returns: "I'll process your refund"
5. WismoAgent combines: "Sorry for delay. I've processed your refund."
```

## Implementation

### Step 1: Add one tool to your agent

```python
from core.agent_tool import call_agent, CALL_AGENT_SCHEMA

class WismoAgent(ConversationalAgent):
    def __init__(self):
        super().__init__(name="wismo")
        self._tool_schemas = [
            # ... your existing tools ...
            CALL_AGENT_SCHEMA,  # Add this one line
        ]
        self._tool_executors = {
            # ... your existing executors ...
            "call_agent": lambda agent_name, customer_message, **kwargs:
                call_agent(agent_name, customer_message, kwargs.get("state")),
        }
```

### Step 2: Update system prompt (optional)

Add one line to your system prompt:

```
If the customer mentions multiple issues, use call_agent to handle 
the other parts, then combine everything into one response.
```

### Step 3: Done

The LLM will automatically use `call_agent` when it detects multiple requests.

## Example Flow

**Customer:** "Cancel my subscription AND refund my last order"

**SubscriptionAgent:**
1. Handles cancellation
2. Detects refund request
3. Calls `call_agent("refund", "customer wants refund for last order")`
4. RefundAgent processes refund, returns result
5. SubscriptionAgent: "I've cancelled your subscription and processed your refund."

## Why This Is Better

✅ **One pattern** - no consultation vs handoff vs delegation confusion  
✅ **One tool** - just `call_agent`  
✅ **Automatic** - LLM decides when to use it  
✅ **Simple** - agents just call other agents  
✅ **Works** - handles multiple requests in one response  

## That's It

No handoff mechanism.  
No delegation pattern.  
No consultation vs delegation distinction.  

Just: **agents can call other agents as tools.**
