# Docker setup

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose) installed and running.
- **backend/.env** with at least `OPENAI_API_KEY` set (see below).

## 1. Environment

Ensure `backend/.env` exists. If not:

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and set:

- **OPENAI_API_KEY** (required) – your OpenAI API key.
- **API_URL** – optional; leave as-is or set to your backend URL.
- MinIO / LangSmith – optional.

Docker Compose will load `backend/.env` into the backend container via `env_file`.

## 2. Build and run

From the **project root** (where `docker-compose.yml` is):

```bash
docker-compose up --build
```

First run will build backend and frontend images and start both services.

- **Frontend:** http://localhost:3000  
- **Backend API:** http://localhost:8000  
- **API docs:** http://localhost:8000/docs  

## 3. Run in background

```bash
docker-compose up -d --build
```

## 4. Stop

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

## 5. Useful commands

| Command | Description |
|--------|-------------|
| `docker-compose logs -f` | Follow logs (all services) |
| `docker-compose logs -f backend` | Backend logs only |
| `docker-compose logs -f frontend` | Frontend logs only |
| `docker-compose restart backend` | Restart backend |
| `docker-compose exec backend bash` | Shell in backend container |
| `docker-compose exec backend pytest` | Run backend tests |

## Troubleshooting

- **“Cannot connect to Docker daemon”** – Start Docker Desktop and wait until it’s fully up.
- **Port 3000 or 8000 in use** – Stop the process using that port or change the host port in `docker-compose.yml` (e.g. `"3001:3000"`).
- **Backend fails to start** – Check `backend/.env` exists and `OPENAI_API_KEY` is set; run `docker-compose logs backend`.
- **Frontend can’t reach backend** – Backend must be healthy first (`depends_on` + healthcheck). Ensure nothing else is bound to port 8000.

More detail: `backend/docs/README_DOCKER.md`.

---

## Running on your server

Use the same `docker-compose.yml` on the server. Set the **public** URL the browser will use to call your API so the frontend is built with the correct API base URL.

### 1. Set the public API URL

The frontend bakes `NEXT_PUBLIC_API_URL` at **build time**, so set it before building on the server.

**Option A – env file (recommended)**  
Create a `.env` file in the **project root** (next to `docker-compose.yml`):

```bash
# .env (project root, for docker-compose)
NEXT_PUBLIC_API_URL=https://api.yourserver.com
```

Replace `https://api.yourserver.com` with the real URL users’ browsers use to reach your API (e.g. `https://lookfor.example.com/api` or `https://backend.yourserver.com`).

**Option B – export before build**

```bash
export NEXT_PUBLIC_API_URL=https://api.yourserver.com
docker-compose up -d --build
```

### 2. Build and run on the server

```bash
# From project root on the server
docker-compose up -d --build
```

Always **rebuild** the frontend when you change `NEXT_PUBLIC_API_URL`:

```bash
docker-compose up -d --build frontend
```

### 3. Backend env on the server

Keep `backend/.env` on the server with:

- `OPENAI_API_KEY`
- `API_URL` (if the backend calls another API)
- MinIO / LangSmith if you use them

Compose loads it via `env_file: ./backend/.env`.

### 4. Reverse proxy and HTTPS (optional)

For HTTPS and a single domain, put a reverse proxy (e.g. Nginx or Caddy) in front:

- `https://yourserver.com` → frontend (container port 3000)
- `https://yourserver.com/api` or `https://api.yourserver.com` → backend (container port 8000)

Then set `NEXT_PUBLIC_API_URL` to that public API URL (e.g. `https://yourserver.com/api` or `https://api.yourserver.com`).

### 5. Persistence on the server

- **Backend data:** Stored in the `backend-data` volume and (if present) in `./backend/state.db` on the host. Back up that file or volume on the server.
- To use only a volume for the DB instead of a host path, you can change the backend service to use a named volume for `state.db` and copy or migrate existing data into it.
