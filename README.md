# 🎯 Fidelio - Multi-Agent Customer Support System

A production-ready AI-powered customer support system with 8 specialized agents for e-commerce support. Built with FastAPI, LangGraph, and Next.js.

## 🚀 Quick Start (3 Steps)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/atadagg/Lookfor_Hackathon_2026_Munich.git
cd Lookfor_Hackathon_2026_Munich
```

### 2️⃣ Configure Environment
```bash
# Copy the example environment file
cp .env.example backend/.env

# Edit backend/.env and add your OpenAI API key
# Required: OPENAI_API_KEY=your_actual_key_here
```

**⚠️ CRITICAL:** You must set `OPENAI_API_KEY` in `backend/.env` or the backend will fail to start.

### 3️⃣ Run with Docker
```bash
# Start all services (backend + frontend)
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

**That's it!** 🎉

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

### Multi-Agent System (8 Specialized Agents)

1. **UC1: WISMO** - "Where is my order?" tracking and delivery status
2. **UC2: Wrong Item** - Wrong/missing item with photo upload support
3. **UC3: Product Issue** - Product quality and performance issues
4. **UC4: Refund** - Full refund processing and store credit
5. **UC5: Order Modification** - Order cancellation and address updates
6. **UC6: Positive Feedback** - Customer appreciation and review requests
7. **UC7: Subscription** - SKIO subscription management (pause/cancel/skip)
8. **UC8: Discount** - Discount code generation and offers

### Technology Stack

**Backend:**
- FastAPI (Python 3.11)
- LangGraph (Multi-agent orchestration)
- OpenAI GPT-4o-mini
- SQLite (State persistence)
- MinIO (Image storage)

**Frontend:**
- Next.js 14 (App Router)
- React
- TypeScript
- Tailwind CSS

**Infrastructure:**
- Docker & Docker Compose
- Health monitoring
- Multi-stage builds
- Production-ready setup

---

## 📋 Prerequisites

- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ (usually included with Docker Desktop)
- **OpenAI API Key**: Get one at [OpenAI Platform](https://platform.openai.com/)

---

## 🛠️ Development

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Access Containers
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 🧪 Testing

### Test with Real Customer Tickets
The system includes 66 real anonymized customer tickets for testing:

```bash
# Run inside backend container
docker-compose exec backend python tests/test_real_tickets.py 10
```

Results: **100% success rate** with real Hackathon API integration!

### Manual Testing with CURL
```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint (example)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-123",
    "user_id": "user-1",
    "channel": "email",
    "customer_email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "shopify_customer_id": "gid://shopify/Customer/123",
    "message": "Where is my order?"
  }'
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── agents/          # 8 specialized agents
│   │   ├── wismo/       # Order tracking agent
│   │   ├── wrong_item/  # Wrong item agent
│   │   ├── product_issue/
│   │   ├── refund/
│   │   ├── order_mod/
│   │   ├── feedback/
│   │   ├── subscription/
│   │   └── discount_agent/
│   ├── api/             # FastAPI server
│   ├── core/            # Base classes & state
│   ├── router/          # Intelligent routing
│   ├── tools/           # Shopify & SKIO tools
│   ├── data/            # Test tickets
│   └── tests/           # Test suites
├── frontend/            # Next.js UI
│   └── src/
│       ├── app/         # Pages
│       ├── components/  # React components
│       └── lib/         # Utilities
└── docker-compose.yml   # Container orchestration
```

---

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...                # Your OpenAI API key

# Optional
API_URL=https://lookfor-hackathon-backend.onrender.com  # Real API endpoint
LANGCHAIN_TRACING_V2=false           # Enable LangSmith debugging
MINIO_URL=...                        # Photo upload storage
```

### Advanced Configuration

See [README_DOCKER.md](./README_DOCKER.md) for:
- Production deployment
- Resource limits
- Custom ports
- Troubleshooting

---

## 🌟 Features

### ✅ Core Features
- **Intelligent Routing**: Automatically routes tickets to the right agent
- **Real API Integration**: Connects to Shopify & SKIO APIs
- **Multi-turn Conversations**: Maintains context across messages
- **Photo Upload**: Customers can attach images (UC2: Wrong Item)
- **State Persistence**: SQLite-based conversation storage
- **Health Monitoring**: Built-in health checks

### ✅ Production Ready
- **Dockerized**: One-command deployment
- **Scalable**: Multi-agent architecture
- **Tested**: 100% success rate on 66 real tickets
- **Documented**: Comprehensive API docs at `/docs`
- **Secure**: Non-root containers, input validation

---

## 🐛 Troubleshooting

### Backend won't start
1. Check if `.env` file exists: `ls backend/.env`
2. Verify OPENAI_API_KEY is set: `cat backend/.env | grep OPENAI`
3. Check logs: `docker-compose logs backend`

### Port already in use
Edit `docker-compose.yml` to change ports:
```yaml
ports:
  - "8001:8000"  # Backend: change 8000 to 8001
  - "3001:3000"  # Frontend: change 3000 to 3001
```

### Frontend can't connect to backend
1. Ensure backend is healthy: `docker-compose ps`
2. Test backend: `curl http://localhost:8000/health`
3. Check frontend logs: `docker-compose logs frontend`

### Complete Reset
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

---

## 📚 Documentation

- **[README_DOCKER.md](./README_DOCKER.md)** - Detailed Docker deployment guide
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when running)
- **[backend/docs/](./backend/docs/)** - Technical documentation
  - API Reference
  - Testing guides
  - Tool specifications

---

## 🤝 Team

Built for **Lookfor Hackathon 2026 Munich** 🇩🇪

---

## 📄 License

This project was created for the Lookfor Hackathon 2026.

---

## 🆘 Support

If you encounter issues:

1. Check this README's troubleshooting section
2. Read [README_DOCKER.md](./README_DOCKER.md)
3. Review logs: `docker-compose logs`
4. Ensure `.env` is configured correctly

---

## ✨ Quick Verification

After starting, verify everything works:

```bash
# 1. Check services are running
docker-compose ps

# 2. Test backend health
curl http://localhost:8000/health

# 3. Test frontend
curl -I http://localhost:3000

# 4. Open in browser
open http://localhost:3000
```

You should see:
- ✅ Backend: `{"status":"healthy","service":"fidelio-backend"}`
- ✅ Frontend: HTTP 200 response
- ✅ Browser: Dashboard interface

---

**🎉 Ready for the Hackathon!**
