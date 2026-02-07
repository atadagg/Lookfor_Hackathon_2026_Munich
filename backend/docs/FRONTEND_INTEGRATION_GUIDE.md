# Frontend Integration Guide - Photo Upload Feature

## Quick Start

This guide shows how to integrate photo uploads for the **Wrong Item** support workflow (UC2).

---

## 🚀 Implementation Steps

### 1. Upload Photo to MinIO

```javascript
async function uploadPhoto(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/photos/upload', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Upload failed');
  }
  
  const result = await response.json();
  return result.url; // MinIO URL
}
```

### 2. Send Message with Photos

```javascript
async function sendMessageWithPhotos(message, photoFiles) {
  // Step 1: Upload all photos
  const photoUrls = [];
  for (const file of photoFiles) {
    const url = await uploadPhoto(file);
    photoUrls.push(url);
  }
  
  // Step 2: Send chat message
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      user_id: userId,
      channel: 'email',
      customer_email: email,
      first_name: firstName,
      last_name: lastName,
      shopify_customer_id: shopifyId,
      message: message,
      photo_urls: photoUrls, // ✅ Include photo URLs
    }),
  });
  
  return await response.json();
}
```

---

## 📱 Complete React Component Example

```tsx
import React, { useState } from 'react';

interface ChatWithPhotosProps {
  conversationId: string;
  userId: string;
  customerEmail: string;
  firstName: string;
  lastName: string;
  shopifyCustomerId: string;
}

export function ChatWithPhotos(props: ChatWithPhotosProps) {
  const [message, setMessage] = useState('');
  const [photos, setPhotos] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploading(true);

    try {
      // Upload photos
      const photoUrls: string[] = [];
      if (photos) {
        for (let i = 0; i < photos.length; i++) {
          const formData = new FormData();
          formData.append('file', photos[i]);

          const uploadRes = await fetch('/photos/upload', {
            method: 'POST',
            body: formData,
          });

          if (uploadRes.ok) {
            const uploadData = await uploadRes.json();
            photoUrls.push(uploadData.url);
          }
        }
      }

      // Send chat message
      const chatRes = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: props.conversationId,
          user_id: props.userId,
          channel: 'email',
          customer_email: props.customerEmail,
          first_name: props.firstName,
          last_name: props.lastName,
          shopify_customer_id: props.shopifyCustomerId,
          message: message,
          photo_urls: photoUrls,
        }),
      });

      const chatData = await chatRes.json();
      setResponse(chatData);
      
      // Clear form
      setMessage('');
      setPhotos(null);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="chat-with-photos">
      <form onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe your issue..."
          required
        />
        
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => setPhotos(e.target.files)}
        />
        
        <button type="submit" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Send Message'}
        </button>
      </form>

      {response && (
        <div className="response">
          <h3>Agent Response:</h3>
          <p>{response.state?.last_assistant_message}</p>
        </div>
      )}
    </div>
  );
}
```

---

## 🎯 Key Points

### 1. File Constraints
- **Max size:** 10MB per photo
- **Allowed types:** Images only (jpg, png, gif, webp, etc.)
- **Multiple uploads:** Supported

### 2. Upload Flow
```
User selects photo → Upload to MinIO → Get URL → Send with chat message
```

### 3. Response Format
```json
{
  "conversation_id": "conv-123",
  "agent": "wrong_item",
  "state": {
    "last_assistant_message": "Thanks for the photo! ...",
    "photo_urls": ["https://storage.aimentora.com/..."],
    "internal_data": {
      "photos_received": true,
      "photo_urls": ["https://storage.aimentora.com/..."]
    }
  }
}
```

---

## 🔍 Error Handling

```javascript
async function uploadPhotoSafely(file) {
  try {
    // Validate file size
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new Error('File too large. Maximum size is 10MB.');
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      throw new Error('Only image files are allowed.');
    }

    // Upload
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/photos/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    const result = await response.json();
    return result.url;

  } catch (error) {
    console.error('Upload error:', error);
    // Show error to user
    alert(error.message);
    return null;
  }
}
```

---

## 🧪 Testing

### Test Photo Upload

```bash
# Terminal test
curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg"
```

### Test Chat with Photo

```bash
# 1. Upload photo
PHOTO_URL=$(curl -X POST "http://localhost:8000/photos/upload" \
  -F "file=@test_image.jpg" | jq -r '.url')

# 2. Send chat with photo
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-123",
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

## 📚 Additional Resources

- **Full API Docs:** See `PHOTO_UPLOAD_API.md`
- **CURL Examples:** See `tests/CURL_TESTS.md`
- **Backend Code:** `api/server.py`, `utils/minio_client.py`
- **Agent Logic:** `agents/wrong_item/graph.py`

---

## 🎨 UI/UX Recommendations

### Photo Preview
```jsx
{photos && Array.from(photos).map((file, i) => (
  <div key={i} className="photo-preview">
    <img src={URL.createObjectURL(file)} alt={`Preview ${i}`} />
    <span>{file.name}</span>
  </div>
))}
```

### Progress Indicator
```jsx
{uploading && (
  <div className="upload-progress">
    Uploading {photos?.length || 0} photo(s)...
  </div>
)}
```

### Success Message
```jsx
{photoUrls.length > 0 && (
  <div className="success">
    ✅ {photoUrls.length} photo(s) uploaded successfully
  </div>
)}
```

---

## ⚙️ Environment Setup

Make sure backend `.env` includes:

```bash
MINIO_ENDPOINT=storage.aimentora.com
MINIO_BUCKET=gangbucket
MINIO_ACCESS_KEY=your_key
MINIO_SECRET_KEY=your_secret
MINIO_USE_SSL=true
```

---

## 🤝 Support

Questions? Check:
1. `PHOTO_UPLOAD_API.md` - Full API documentation
2. `tests/test_photo_upload.py` - Test examples
3. Backend team for MinIO credentials
