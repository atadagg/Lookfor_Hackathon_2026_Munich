# Backend Documentation

## 📚 Documentation Files

| File | Description |
|------|-------------|
| **HACKATHON_API_REFERENCE.md** | Complete reference for all 18 hackathon API tools |
| **MINIO_INTEGRATION_SUMMARY.md** | MinIO photo upload integration guide (UC2) |

## 🧪 Testing

All test files are in `backend/tests/`:
- **CURL_TESTS.md** - CURL commands for all use cases (updated for real API)
- **test_api_direct.py** - Direct tool testing script
- **test_real_api_comprehensive.py** - Full integration test
- **run_api_test.sh** - Automated test runner

## 🎯 Quick Start

### Test with Real API

1. **Set API URL** in `backend/.env`:
   ```bash
   API_URL=https://lookfor-hackathon-backend.onrender.com
   ```

2. **Restart backend**:
   ```bash
   uvicorn api.server:app --reload
   ```

3. **Run CURL tests**:
   ```bash
   cd backend/tests
   # Check CURL_TESTS.md for all test commands
   ```

### Test Tools Directly

```bash
cd backend/tests
python3 test_api_direct.py
```

## 🔧 Tools

### Shopify Tools (13)
All tools call `/hackathon/...` endpoints when `API_URL` is set.

See **HACKATHON_API_REFERENCE.md** for complete details on:
- Request/response formats
- Parameters
- Examples
- Error handling

### Skio Tools (5)
Subscription management tools for UC7.

## 📊 API Modes

### Mock Mode
- **When**: `API_URL` is empty or not set in `.env`
- **Behavior**: Tools return mock data
- **Use for**: Local testing, development

### Real API Mode  
- **When**: `API_URL` is set to hackathon endpoint
- **Behavior**: Tools make real HTTP calls to API
- **Use for**: Integration testing, hackathon deployment

## 🎯 Use Cases Covered

1. **UC1: WISMO** - Where Is My Order
2. **UC2: Wrong Item** - Wrong/Missing items (with photo upload)
3. **UC3: Product Issue** - Product not working
4. **UC4: Refund Request** - Customer refunds
5. **UC5: Order Modification** - Cancel/change orders
6. **UC6: Feedback** - Positive feedback
7. **UC7: Subscription** - Subscription management
8. **UC8: Discount** - Discount code requests

Each use case has:
- ✅ LangGraph-based agent
- ✅ Dedicated tools
- ✅ Test suite
- ✅ CURL examples

## 📁 Project Structure

```
backend/
├── agents/          # 8 specialist agents (UC1-UC8)
├── api/             # FastAPI server
├── core/            # Base classes, state management
├── router/          # Intent classification
├── tools/           # Shopify & Skio tools
├── tests/           # All tests and test scripts
└── docs/            # This documentation
```

## ✅ Ready for Hackathon

All 18 tools are updated and ready to use the real hackathon API. Just set `API_URL` in `.env` and restart the backend!
