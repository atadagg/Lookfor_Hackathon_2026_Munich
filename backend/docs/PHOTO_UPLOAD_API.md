# Photo Upload API Documentation

## Overview

This API enables customers to upload photos for the **Wrong Item** support workflow (UC2). Photos are stored in MinIO and passed to the AI agent for context-aware responses.

---

## Endpoints

### 1. Upload Photo

**Endpoint:** `POST /photos/upload`

**Description:** Upload a customer photo to MinIO storage.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file`: Image file (jpg, png, gif, etc.)

**Constraints:**
- Maximum file size: 10MB
- Allowed types: Images only (validated by content-type)

**Response:**
```json
{
  "success": true,
  "url": "https://storage.aimentora.com/api/v1/download-shared-object/gangbucket/_uuid.jpg",
  "filename": "_a1b2c3d4-5678-90ef-ghij-klmnopqrstuv.jpg",
  "uploaded_at": "2026-02-06T22:45:00.123456"
}
```

**Error Response:**
```json
{
  "detail": "Invalid file type: application/pdf. Only images are allowed."
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@/path/to/photo.jpg"
```

**Example (JavaScript/Frontend):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/photos/upload', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
console.log('Photo URL:', result.url);
```

**Example (Python/httpx):**
```python
import httpx

async with httpx.AsyncClient() as client:
    with open("photo.jpg", "rb") as f:
        response = await client.post(
            "http://localhost:8000/photos/upload",
            files={"file": ("photo.jpg", f, "image/jpeg")}
        )
    result = response.json()
    print(result["url"])
```

---

### 2. Download Photo

**Endpoint:** `GET /photos/download`

**Description:** Retrieve a photo from MinIO storage.

**Query Parameters:**
- `url` (required): Full MinIO URL of the photo

**Response:**
- Binary image data with appropriate `Content-Type` header

**Example (curl):**
```bash
curl -X GET "http://localhost:8000/photos/download?url=https://storage.aimentora.com/..." \
  --output downloaded_photo.jpg
```

**Example (JavaScript/Frontend):**
```javascript
const photoUrl = "https://storage.aimentora.com/api/v1/download-shared-object/...";
const response = await fetch(`http://localhost:8000/photos/download?url=${encodeURIComponent(photoUrl)}`);
const blob = await response.blob();
const imageUrl = URL.createObjectURL(blob);
```

---

## Integration with Chat API

### Sending Photos with Messages

When sending a chat message that includes photos, include the `photo_urls` field:

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "user_id": "user-456",
    "channel": "email",
    "customer_email": "customer@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "shopify_customer_id": "cust-789",
    "message": "I received the wrong item. Photo attached.",
    "photo_urls": [
      "https://storage.aimentora.com/api/v1/download-shared-object/gangbucket/_uuid1.jpg",
      "https://storage.aimentora.com/api/v1/download-shared-object/gangbucket/_uuid2.jpg"
    ]
  }'
```

**Frontend Workflow:**
1. User selects photo(s) via file input
2. Upload each photo via `POST /photos/upload`
3. Collect the returned URLs
4. Send chat message with `photo_urls` array

**Example (React/TypeScript):**
```typescript
async function handleSubmitWithPhotos(
  message: string,
  files: FileList
): Promise<void> {
  // Step 1: Upload all photos
  const photoUrls: string[] = [];
  
  for (let i = 0; i < files.length; i++) {
    const formData = new FormData();
    formData.append('file', files[i]);
    
    const uploadResponse = await fetch('/photos/upload', {
      method: 'POST',
      body: formData,
    });
    
    if (uploadResponse.ok) {
      const result = await uploadResponse.json();
      photoUrls.push(result.url);
    }
  }
  
  // Step 2: Send chat message with photo URLs
  const chatResponse = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      user_id: userId,
      channel: 'email',
      customer_email: customerEmail,
      first_name: firstName,
      last_name: lastName,
      shopify_customer_id: shopifyCustomerId,
      message: message,
      photo_urls: photoUrls,
    }),
  });
  
  const chatResult = await chatResponse.json();
  console.log('Agent response:', chatResult);
}
```

---

## AI Agent Behavior

### How Photos Are Processed

1. **Storage:** Photos are uploaded to MinIO and receive a public URL
2. **State Tracking:** Photo URLs are stored in `AgentState.photo_urls`
3. **Agent Detection:** The Wrong Item agent detects photos in `internal_data.photos_received`
4. **LLM Context:** Photos are sent to the LLM using vision capabilities:
   ```python
   messages = [
     {"role": "system", "content": system_prompt},
     {
       "role": "user",
       "content": [
         {"type": "text", "text": user_prompt},
         {"type": "image_url", "image_url": {"url": photo_url, "detail": "low"}}
       ]
     }
   ]
   ```
5. **Response:** Agent acknowledges photos and provides context-aware responses

### Agent Response Examples

**Without Photo:**
```
"I'm sorry to hear that! To get this sorted fast, could you tell me 
whether something is missing or you received the wrong item? 
If you can, send a photo of what you received—that really helps."
```

**With Photo:**
```
"I'm sorry to hear that. Thanks for sharing the photo—that helps a lot! 
We can fix this in a few ways: I can arrange a free resend of the 
correct item, or offer you store credit (item value + 10% bonus), 
or process a refund to your original payment method. Which do you prefer?"
```

---

## Environment Configuration

### Required Environment Variables

Add these to `backend/.env`:

```bash
# MinIO Storage Configuration (UC2: Wrong Item photo uploads)
MINIO_URL=http://storage.aimentora.com/api/v1/download-shared-object/...
MINIO_ENDPOINT=storage.aimentora.com
MINIO_BUCKET=gangbucket
MINIO_ACCESS_KEY=your_access_key_here
MINIO_SECRET_KEY=your_secret_key_here
MINIO_USE_SSL=true
```

### Mock Mode

If `MINIO_ACCESS_KEY` is not set, the upload endpoint operates in **mock mode**:
- Returns a mock URL from `MINIO_URL` environment variable
- Does not perform actual upload
- Useful for local development and testing

---

## Testing

### Test Photo Upload

```bash
# Upload a test photo
curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg" | jq

# Expected output:
# {
#   "success": true,
#   "url": "https://storage.aimentora.com/...",
#   "filename": "_uuid.jpg"
# }
```

### Test Chat with Photo

```bash
# First, upload photo and capture URL
PHOTO_URL=$(curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg" | jq -r '.url')

# Then send chat with photo URL
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-photo-123",
    "user_id": "user-001",
    "customer_email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "shopify_customer_id": "cust-001",
    "message": "Wrong item received, photo attached",
    "photo_urls": ["'"$PHOTO_URL"'"]
  }' | jq
```

---

## Security Considerations

1. **File Size Limits:** Enforced at 10MB to prevent abuse
2. **File Type Validation:** Only image types are accepted
3. **Unique Filenames:** UUIDs prevent filename collisions
4. **Public URLs:** Photos are publicly accessible via MinIO URL (consider signed URLs for production)

---

## Troubleshooting

### Upload Fails with 400 Error

**Problem:** `"Invalid file type"`
**Solution:** Ensure the file is an image (jpg, png, gif, webp, etc.)

### Upload Fails with 500 Error

**Problem:** MinIO credentials invalid or connection failed
**Solution:** Check `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and `MINIO_ENDPOINT` in `.env`

### Photos Not Detected by Agent

**Problem:** Agent doesn't acknowledge photos in response
**Solution:** Ensure `photo_urls` array is included in the chat request body

### LLM Doesn't Process Photos

**Problem:** Vision capabilities not working
**Solution:** Verify you're using `gpt-4o-mini` or another vision-capable model

---

## API Reference Summary

| Endpoint | Method | Purpose | Request Body | Response |
|----------|--------|---------|--------------|----------|
| `/photos/upload` | POST | Upload photo | `multipart/form-data` with `file` | `{success, url, filename}` |
| `/photos/download` | GET | Download photo | Query param: `url` | Binary image data |
| `/chat` | POST | Send message with photos | JSON with `photo_urls` array | Agent response |

---

## Support

For questions or issues with photo uploads, contact the backend team or check the MinIO documentation at https://min.io/docs/
