# 🚦 Onboarding Checklist

Use this checklist when setting up the project for the first time.

## ✅ Pre-Setup

- [ ] Docker Desktop installed and running
- [ ] OpenAI API key ready (get from https://platform.openai.com/)
- [ ] Git installed

## ✅ Setup Steps

### Step 1: Clone & Navigate
```bash
git clone https://github.com/atadagg/Lookfor_Hackathon_2026_Munich.git
cd Lookfor_Hackathon_2026_Munich
```
- [ ] Repository cloned successfully
- [ ] In correct directory

### Step 2: Configure Environment
```bash
cp .env.example backend/.env
```
- [ ] `.env.example` copied to `backend/.env`

Now edit `backend/.env`:
```bash
# Open with your editor
nano backend/.env    # or: code backend/.env, vim backend/.env
```

**REQUIRED CHANGE:**
```bash
# Change this line:
OPENAI_API_KEY=your_openai_api_key_here

# To your actual key:
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

- [ ] `OPENAI_API_KEY` set to actual key
- [ ] File saved

### Step 3: Start Services
```bash
docker-compose up --build
```
- [ ] Command running without errors
- [ ] See "Backend started" messages
- [ ] See "Frontend ready" messages
- [ ] Both containers show as `healthy` or `running`

---

## ✅ Verification

Open a **new terminal** and run these tests:

### Test 1: Backend Health
```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"healthy","service":"fidelio-backend"}
```
- [ ] Backend responds with healthy status

### Test 2: Frontend Access
```bash
curl -I http://localhost:3000
```

**Expected Output:**
```
HTTP/1.1 200 OK
...
```
- [ ] Frontend responds with 200 OK

### Test 3: Browser Access
Open browser to: http://localhost:3000

- [ ] Dashboard loads successfully
- [ ] No console errors
- [ ] Can see conversation interface

### Test 4: API Documentation
Open browser to: http://localhost:8000/docs

- [ ] Swagger UI loads
- [ ] Can see `/chat` endpoint
- [ ] Can see `/health` endpoint

### Test 5: Simple Chat Request
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-onboarding",
    "user_id": "newuser-1",
    "channel": "email",
    "customer_email": "test@example.com",
    "first_name": "New",
    "last_name": "User",
    "shopify_customer_id": "gid://shopify/Customer/123",
    "message": "Where is my order #1234?"
  }'
```

**Expected:** JSON response with agent routing information
- [ ] Request returns 200 status
- [ ] Response includes `"agent"` field
- [ ] Response includes conversation data

---

## ✅ Common Issues & Solutions

### Issue: "Cannot connect to Docker daemon"
**Solution:** Start Docker Desktop and wait for it to fully load

### Issue: "Port 8000 already in use"
**Solution:** 
```bash
# Find what's using the port
lsof -i :8000

# Kill it or change port in docker-compose.yml
```

### Issue: Backend shows "unhealthy"
**Solution:**
```bash
# Check logs
docker-compose logs backend

# Common fix: Missing API key
# Verify: cat backend/.env | grep OPENAI_API_KEY
```

### Issue: "Module not found" errors
**Solution:**
```bash
# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

---

## ✅ Final Checklist

Before considering setup complete:

- [ ] Both services running (backend + frontend)
- [ ] Backend health check passes
- [ ] Frontend accessible in browser
- [ ] API docs load correctly
- [ ] Test chat request succeeds
- [ ] No error messages in logs

---

## 🎉 Success!

If all checkboxes are marked, you're ready to:
- Develop new features
- Test with real customer tickets
- Present at the hackathon

---

## 📞 Need Help?

1. Check `README.md` troubleshooting section
2. Review `README_DOCKER.md` for detailed info
3. Check logs: `docker-compose logs -f`
4. Ask your team members

---

## ⏱️ Expected Setup Time

- **First time**: ~10-15 minutes (including Docker downloads)
- **After first time**: ~2-3 minutes

---

**Last Updated:** 2026-02-07
