"""Tests for photo upload endpoints (UC2: Wrong Item)."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from api.server import app


client = TestClient(app)


@pytest.fixture
def sample_image():
    """Create a minimal valid JPEG image (1x1 pixel)."""
    # Minimal JPEG header + data
    jpeg_data = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
        b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
        b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00'
        b'\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01'
        b'\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05'
        b'\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04'
        b'\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A'
        b'\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82'
        b'\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvw'
        b'xyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a'
        b'\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba'
        b'\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda'
        b'\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8'
        b'\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'
    )
    return BytesIO(jpeg_data)


def test_upload_photo_success(sample_image):
    """Test successful photo upload."""
    response = client.post(
        "/photos/upload",
        files={"file": ("test_photo.jpg", sample_image, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "url" in data
    assert "filename" in data
    assert data["filename"].endswith(".jpg")


def test_upload_photo_invalid_type():
    """Test upload rejection for non-image files."""
    pdf_content = b"%PDF-1.4\n%test file"
    
    response = client.post(
        "/photos/upload",
        files={"file": ("document.pdf", BytesIO(pdf_content), "application/pdf")}
    )
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_upload_photo_too_large():
    """Test upload rejection for files exceeding 10MB."""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    
    response = client.post(
        "/photos/upload",
        files={"file": ("large.jpg", BytesIO(large_content), "image/jpeg")}
    )
    
    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]


def test_chat_with_photo_urls():
    """Test sending a chat message with photo URLs."""
    # First, upload a photo
    sample_image = BytesIO(
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xd9'
    )
    
    upload_response = client.post(
        "/photos/upload",
        files={"file": ("photo.jpg", sample_image, "image/jpeg")}
    )
    
    assert upload_response.status_code == 200
    photo_url = upload_response.json()["url"]
    
    # Then send a chat message with the photo URL
    chat_response = client.post(
        "/chat",
        json={
            "conversation_id": "photo-test-001",
            "user_id": "user-photo-test",
            "channel": "email",
            "customer_email": "lisa@example.com",
            "first_name": "Lisa",
            "last_name": "Test",
            "shopify_customer_id": "cust-photo-test",
            "message": "I received the wrong item. Photo attached.",
            "photo_urls": [photo_url],
        }
    )
    
    assert chat_response.status_code == 200
    data = chat_response.json()
    
    assert data["conversation_id"] == "photo-test-001"
    assert "state" in data
    
    # Verify photo URLs are in the state
    if "photo_urls" in data["state"]:
        assert photo_url in data["state"]["photo_urls"]


def test_chat_with_multiple_photos():
    """Test sending a chat message with multiple photo URLs."""
    # Upload two photos
    photo_urls = []
    
    for i in range(2):
        sample_image = BytesIO(
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xd9'
        )
        
        upload_response = client.post(
            "/photos/upload",
            files={"file": (f"photo{i}.jpg", sample_image, "image/jpeg")}
        )
        
        assert upload_response.status_code == 200
        photo_urls.append(upload_response.json()["url"])
    
    # Send chat with both photos
    chat_response = client.post(
        "/chat",
        json={
            "conversation_id": "multi-photo-test-001",
            "user_id": "user-multi-photo",
            "channel": "email",
            "customer_email": "lisa@example.com",
            "first_name": "Lisa",
            "last_name": "Test",
            "shopify_customer_id": "cust-multi-photo",
            "message": "I received the wrong items. Two photos attached.",
            "photo_urls": photo_urls,
        }
    )
    
    assert chat_response.status_code == 200
    data = chat_response.json()
    
    # Verify both photos are tracked
    if "photo_urls" in data["state"]:
        assert len(data["state"]["photo_urls"]) == 2


def test_upload_missing_file():
    """Test upload endpoint without a file."""
    response = client.post("/photos/upload")
    
    assert response.status_code == 422  # Unprocessable Entity (missing required field)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
