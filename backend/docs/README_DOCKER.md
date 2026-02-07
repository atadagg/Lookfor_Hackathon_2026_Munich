# 🐳 Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker (20.10+)
- Docker Compose (2.0+)

### 1. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example backend/.env
```

Edit `backend/.env` with your actual credentials:
- `OPENAI_API_KEY`: Your OpenAI API key
- `API_URL`: Hackathon API endpoint (default: https://lookfor-hackathon-backend.onrender.com)
- Optional: MinIO, LangSmith credentials

### 2. Build and Run

Build and start all services:

```bash
docker-compose up --build
```

Or run in detached mode (background):

```bash
docker-compose up -d --build
```

### 3. Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Stop Services

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

---

## Development Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart a Service

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Rebuild a Service

```bash
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

### Execute Commands in Container

```bash
# Backend shell
docker-compose exec backend bash

# Run tests in backend
docker-compose exec backend pytest

# Frontend shell
docker-compose exec frontend sh
```

---

## Architecture

### Services

#### Backend (`fidelio-backend`)
- **Port**: 8000
- **Framework**: FastAPI + LangGraph
- **Features**: Multi-agent orchestration, Real Hackathon API integration
- **Health Check**: `curl http://localhost:8000/health`

#### Frontend (`fidelio-frontend`)
- **Port**: 3000
- **Framework**: Next.js 14 (App Router)
- **Features**: Real-time chat UI, Conversation management

### Volumes

- `backend-data`: Persistent storage for backend data
- `backend/state.db`: SQLite database mounted from host

### Network

- `fidelio-network`: Internal bridge network for service communication

---

## Troubleshooting

### Backend not starting

1. Check if `.env` file exists in `backend/` folder
2. Verify OPENAI_API_KEY is set
3. Check logs: `docker-compose logs backend`

```bash
docker-compose logs backend
```

### Frontend can't connect to backend

1. Verify backend is healthy:
```bash
curl http://localhost:8000/health
```

2. Check if services are on the same network:
```bash
docker-compose ps
```

### Port already in use

If ports 3000 or 8000 are already in use, modify `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8000 to 8001
  
  frontend:
    ports:
      - "3001:3000"  # Change 3000 to 3001
```

### Database issues

Remove and recreate the database volume:

```bash
docker-compose down -v
docker-compose up --build
```

### Clean rebuild

Remove all containers, volumes, and rebuild from scratch:

```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

---

## Production Deployment

### Environment Variables

For production, update these variables:

```bash
# backend/.env
NODE_ENV=production
API_URL=<your-production-api-url>
```

### Build for Production

```bash
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d
```

### Resource Limits

Add resource constraints in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Testing with Real API

The backend automatically connects to the real Hackathon API when `API_URL` is set in `.env`.

Test with real customer tickets:

```bash
docker-compose exec backend python tests/test_real_tickets.py 10
```

---

## Health Checks

Backend includes automatic health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

Check health status:

```bash
docker-compose ps
```

Healthy services show `healthy` in the status column.

---

## 🚀 Ready for Hackathon!

Your multi-agent system is now running in Docker containers with:
- ✅ Real API integration
- ✅ Multi-agent orchestration (8 use cases)
- ✅ Photo upload support (MinIO)
- ✅ Persistent storage
- ✅ Health monitoring
- ✅ Production-ready setup

Good luck! 🎯
