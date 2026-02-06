# Lookfor Hackathon Support Agent

This is a scaffold for a digital customer support agent composed of:

- **core**: shared state, base agent interface, and persistence stub
- **router**: LLM-based receptionist that triages conversations
- **agents**: specialist graphs (WISMO, subscription, defect, +6 more)
- **api**: FastAPI server exposing a `/chat` endpoint

## Quickstart

```bash
cd lookfor-hackathon
pip install -r requirements.txt
uvicorn api.server:app --reload
# or via docker-compose
# docker compose up --build
```

From here you can plug in LangGraph graphs, real tools (Shopify/CRM),
and production-grade prompts.

## Persistence: SQLite checkpointer

Conversation state and emails are stored in a single SQLite DB (`state.db`) via `core.database.Checkpointer`.

- **Threads** (`threads` table)
  - One row per external conversation (`external_thread_id`).
  - Tracks overall status (`status` = `open` / `escalated` / `closed`), `current_workflow`, `workflow_step`, `is_escalated`, `escalated_at`.
  - Stores the latest full `AgentState` in `state_json`.

- **Messages** (`messages` table)
  - One row per email/chat message.
  - Columns: `thread_id`, `role` (`user` / `assistant` / `system`), `content`, `direction` (`inbound` / `outbound`), timestamps.

Basic usage pattern:

```python
from core.database import Checkpointer

cp = Checkpointer()

# Log incoming user email
cp.save_message(conversation_id, role="user", content=text, direction="inbound")

# Load previous AgentState (if any)
state = cp.load_state(conversation_id) or {}

# ... run router + agent graph, producing updated `state` ...

# Persist updated AgentState + thread status
cp.save_state(conversation_id, state)

# Log outgoing assistant reply
cp.save_message(conversation_id, role="assistant", content=reply, direction="outbound")
```

For LangGraph graphs, compile with the same SQLite DB:

```python
graph = build_shipping_graph()
app = graph.compile(checkpointer=cp.langgraph_saver)
```
