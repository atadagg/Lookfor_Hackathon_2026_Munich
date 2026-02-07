# MinIO Photo Upload Integration - Implementation Summary

## 🎯 Overview

Implemented complete photo upload functionality for **UC2: Wrong Item** workflow, enabling customers to attach photos when reporting wrong/missing items.

---

## ✅ What Was Built

### 1. **MinIO Client Utilities** (`backend/utils/minio_client.py`)
- `upload_photo()` - Upload images to MinIO storage
- `get_photo_url()` - Generate public download URLs
- `download_photo()` - Retrieve images from MinIO
- Mock mode support for local development (when credentials not set)

### 2. **API Endpoints** (`backend/api/server.py`)

#### POST `/photos/upload`
- Accept multipart/form-data file uploads
- Validate file type (images only) and size (max 10MB)
- Generate unique filenames with UUID
- Return MinIO public URL

#### GET `/photos/download`
- Download photos by URL
- Return binary image data with proper content-type

#### Updated POST `/chat`
- Added `photo_urls: Optional[List[str]]` field
- Photos passed through to agent state

### 3. **Agent Integration** (`backend/agents/wrong_item/graph.py`)

#### Photo Detection (`node_decide_step`)
```python
photo_urls = state.get("photo_urls", [])
if photo_urls:
    internal["photos_received"] = True
    internal["photo_urls"] = photo_urls
```

#### LLM Vision Integration (`node_generate_response`)
```python
# Send photos to LLM using vision API
content_parts = [{"type": "text", "text": user_prompt}]
for photo_url in photo_urls:
    content_parts.append({
        "type": "image_url",
        "image_url": {"url": photo_url, "detail": "low"}
    })
```

#### Smart Response
- Thanks customer when photos are provided
- Includes photo context in workflow decisions
- LLM can "see" the photos and provide context-aware responses

### 4. **Environment Configuration**

#### `.env` / `.env.example`
```bash
MINIO_URL=http://storage.aimentora.com/...
MINIO_ENDPOINT=storage.aimentora.com
MINIO_BUCKET=gangbucket
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_USE_SSL=true
```

### 5. **Documentation**

Created comprehensive guides:
- **`PHOTO_UPLOAD_API.md`** - Full API reference with examples
- **`FRONTEND_INTEGRATION_GUIDE.md`** - Quick start for frontend developers
- **`tests/test_photo_upload.py`** - Pytest test suite

### 6. **CURL Test Updates** (`backend/tests/CURL_TESTS.md`)
- Added `MINIO_URL` environment variable to setup
- Updated UC2 multi-turn scenario with photo upload
- Added new Scenario 6: Immediate photo upload in first message

---

## 🔄 Complete Workflow

### Backend Flow
```
1. Frontend uploads photo → POST /photos/upload
2. Backend saves to MinIO → Returns public URL
3. Frontend sends chat with photo_urls → POST /chat
4. Router detects UC2: Wrong Item
5. Wrong Item agent receives photo_urls in state
6. Agent stores photos in internal_data
7. Agent sends photos to LLM via vision API
8. LLM generates context-aware response
9. Response thanks customer for photos
```

### Example Request/Response

**Upload Photo:**
```bash
curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@photo.jpg"

# Response:
{
  "success": true,
  "url": "https://storage.aimentora.com/.../uuid.jpg",
  "filename": "_a1b2c3d4.jpg"
}
```

**Send Chat with Photo:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "customer_email": "user@example.com",
    "message": "Wrong item received, photo attached",
    "photo_urls": ["https://storage.aimentora.com/.../uuid.jpg"]
  }'

# Response includes:
{
  "state": {
    "last_assistant_message": "Thanks for the photo—that helps a lot! ...",
    "photo_urls": ["https://storage.aimentora.com/.../uuid.jpg"],
    "internal_data": {
      "photos_received": true
    }
  }
}
```

---

## 🧪 Testing

### Unit Tests
```bash
pytest backend/tests/test_photo_upload.py -v
```

Tests cover:
- ✅ Successful photo upload
- ✅ Invalid file type rejection
- ✅ File size limit enforcement
- ✅ Chat integration with photos
- ✅ Multiple photo uploads
- ✅ Missing file handling

### Manual Testing
```bash
# 1. Start backend
cd backend
uvicorn api.server:app --reload

# 2. Upload test photo
curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg" | jq

# 3. Send chat with photo
PHOTO_URL=$(curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg" | jq -r '.url')

curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-123",
    "user_id": "user-001",
    "customer_email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "shopify_customer_id": "cust-001",
    "message": "Wrong item, photo attached",
    "photo_urls": ["'"$PHOTO_URL"'"]
  }' | jq
```

---

## 📂 Files Created/Modified

### Created
- `backend/utils/minio_client.py` - MinIO utilities
- `backend/utils/__init__.py` - Utils module init
- `backend/tests/test_photo_upload.py` - Photo upload tests
- `backend/PHOTO_UPLOAD_API.md` - Full API documentation
- `backend/FRONTEND_INTEGRATION_GUIDE.md` - Frontend quick start

### Modified
- `backend/api/server.py` - Added photo upload/download endpoints
- `backend/agents/wrong_item/graph.py` - Photo detection + LLM vision integration
- `backend/agents/wrong_item/prompts.py` - Updated to acknowledge photos
- `backend/.env` - Added MinIO configuration
- `backend/.env.example` - Added MinIO template config
- `backend/tests/CURL_TESTS.md` - Added photo upload examples

---

## 🎨 Agent Behavior Changes

### Before Integration
```
Agent: "I'm sorry to hear that! Could you tell me whether 
something is missing or you received the wrong item? 
If you can, send a photo—that really helps."
```

### After Integration (with photo)
```
Agent: "I'm sorry to hear that. Thanks for sharing the 
photo—that helps a lot! We can fix this in a few ways: 
I can arrange a free resend of the correct item, or offer 
you store credit (item value + 10% bonus), or process a 
refund to your original payment method. Which do you prefer?"
```

The LLM can now:
- ✅ See the actual photo content
- ✅ Provide more accurate responses
- ✅ Acknowledge receipt of photos
- ✅ Make better decisions based on visual information

---

## 🔒 Security Features

1. **File Type Validation** - Only images accepted
2. **Size Limits** - 10MB max per photo
3. **Unique Filenames** - UUID-based naming prevents collisions
4. **Content-Type Validation** - Enforced at API level
5. **Error Handling** - Graceful failures with clear error messages

---

## 🚀 Frontend Integration

### Simple Example
```javascript
// Upload photo
const formData = new FormData();
formData.append('file', photoFile);
const uploadRes = await fetch('/photos/upload', {
  method: 'POST',
  body: formData,
});
const { url } = await uploadRes.json();

// Send chat with photo
await fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ...chatData,
    photo_urls: [url],
  }),
});
```

See `FRONTEND_INTEGRATION_GUIDE.md` for complete React examples.

---

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose | Body | Response |
|----------|--------|---------|------|----------|
| `/photos/upload` | POST | Upload image | `multipart/form-data` | `{success, url, filename}` |
| `/photos/download` | GET | Download image | Query: `url` | Binary image data |
| `/chat` | POST | Send message | JSON + `photo_urls` | Agent response |

---

## 🎯 Use Cases Supported

### UC2: Wrong Item - Complete Photo Workflow
1. ✅ Customer uploads photo of wrong item received
2. ✅ Photo URL sent with complaint message
3. ✅ Agent detects and acknowledges photo
4. ✅ LLM analyzes photo via vision API
5. ✅ Agent provides context-aware response
6. ✅ Photo stored in conversation history
7. ✅ Multi-turn conversations maintain photo context

---

## 🔮 Future Enhancements

Potential improvements:
- [ ] Signed URLs with expiration for better security
- [ ] Image compression/optimization before upload
- [ ] OCR for text extraction from photos
- [ ] Photo metadata extraction (EXIF data)
- [ ] Thumbnail generation
- [ ] Photo gallery in conversation history
- [ ] Support for video attachments

---

## 📞 Support

For issues or questions:
1. Check `PHOTO_UPLOAD_API.md` for API details
2. Review `FRONTEND_INTEGRATION_GUIDE.md` for integration help
3. Run `pytest tests/test_photo_upload.py` to verify setup
4. Contact backend team for MinIO credential issues

---

## ✨ Summary

**Complete photo upload system implemented for UC2: Wrong Item workflow with:**
- ✅ Frontend-friendly upload API
- ✅ MinIO storage integration
- ✅ LLM vision capabilities
- ✅ Agent context awareness
- ✅ Comprehensive documentation
- ✅ Full test coverage
- ✅ Error handling & validation

**Ready for hackathon deployment!** 🚀
