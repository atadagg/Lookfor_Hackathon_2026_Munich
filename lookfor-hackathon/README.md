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
