# Lookfor Hackathon 2026 - Team Fidelio

AI-powered multi-agent customer support system for e-commerce brands.

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd Lookfor_Hackathon_2026_Fidelio

# 2. Add your API keys to backend/.env
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY and API_URL

# 3. Run everything
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## Architecture

```
├── backend/           # Python (FastAPI + LangGraph)
│   ├── api/           # FastAPI server, /chat and /thread endpoints
│   ├── agents/        # 8 specialist agents (WISMO, refund, etc.)
│   ├── core/          # State, database, LLM client, base agent classes
│   ├── router/        # Intent classification / routing
│   ├── schemas/       # Pydantic models
│   ├── tools/         # 18 hackathon tools (Shopify + Skio)
│   └── tests/         # Integration tests
├── frontend/          # Next.js + Shadcn UI dashboard
│   └── src/
│       ├── app/       # App router pages
│       ├── components/# Mail-like UI components
│       └── lib/       # API client
├── docker-compose.yml # One-click orchestration
└── README.md
```

### Agent System

| Agent | Handles |
|-------|---------|
| `wismo` | Shipping delay / Where Is My Order |
| `wrong_item` | Wrong or missing items in parcel |
| `product_issue` | Product "no effect" complaints |
| `refund` | Standard refund requests |
| `order_mod` | Order cancellation & address changes |
| `feedback` | Positive customer feedback |
| `subscription` | Subscription & billing issues (Skio) |
| `discount` | Discount / promo code problems |

### Routing

An LLM-based intent classifier (`router/`) analyzes the customer message and routes to the appropriate specialist agent. Each agent has its own system prompt, tool set, and workflow logic.

### Tools (18 total)

13 Shopify tools + 5 Skio subscription tools, all conforming to the Hackathon Tooling Spec. Tools make HTTP POST calls to `{API_URL}/hackhaton/*` endpoints. When `API_URL` is not set, agents use built-in mock responses for development.

### Escalation

When the workflow manual requires escalation or the system cannot safely proceed:
1. The customer is informed their issue is being escalated
2. A structured `EscalationSummary` is generated (reason, context, recommended action)
3. The thread is marked `is_escalated = true` and automation stops

### Observability (Frontend Dashboard)

The Shadcn UI dashboard provides three views per conversation:
- **Message** tab: Full email thread (customer + AI responses)
- **Agent Trace** tab: Timeline of agent decisions, workflow steps, and tool calls
- **Raw Logs** tab: Complete tool I/O and JSON state snapshot

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `API_URL` | At eval | Hackathon tool endpoint base URL |

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.server:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```
