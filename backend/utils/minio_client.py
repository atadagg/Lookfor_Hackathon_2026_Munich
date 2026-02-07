"""MinIO client utilities for photo upload/download (UC2: Wrong Item).

This module provides functions to interact with MinIO storage for
customer photo attachments in the Wrong Item workflow.
"""

from __future__ import annotations

import os
import uuid
from typing import Optional
import httpx
from datetime import datetime


# MinIO configuration from environment
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "storage.aimentora.com")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "gangbucket")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "true").lower() == "true"


async def upload_photo(file_content: bytes, filename: str) -> dict:
    """
    Upload a photo to MinIO storage.
    
    Args:
        file_content: Binary content of the image file
        filename: Original filename (e.g., "photo.jpg")
    
    Returns:
        dict with:
            - success: bool
            - url: str (public URL if successful)
            - error: str (error message if failed)
    """
    try:
        # Generate unique filename to avoid collisions
        file_ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        unique_filename = f"_{uuid.uuid4()}.{file_ext}"
        
        # Construct MinIO API URL for upload
        protocol = "https" if MINIO_USE_SSL else "http"
        upload_url = f"{protocol}://{MINIO_ENDPOINT}/api/v1/buckets/{MINIO_BUCKET}/objects/upload"
        
        # For hackathon: If MinIO credentials not set, return mock success
        if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
            mock_url = os.getenv("MINIO_URL", "")
            if not mock_url:
                mock_url = f"{protocol}://{MINIO_ENDPOINT}/api/v1/download-shared-object/mock_{unique_filename}"
            
            return {
                "success": True,
                "url": mock_url,
                "filename": unique_filename,
                "message": "Mock mode - no actual upload (MINIO_ACCESS_KEY not set)",
            }
        
        # Prepare multipart form data
        files = {
            "file": (unique_filename, file_content, f"image/{file_ext}"),
        }
        
        headers = {
            "Authorization": f"Bearer {MINIO_ACCESS_KEY}",  # Adjust auth method as needed
        }
        
        # Upload to MinIO
        async with httpx.AsyncClient() as client:
            response = await client.post(
                upload_url,
                files=files,
                headers=headers,
                timeout=30.0,
            )
            
            if response.status_code in (200, 201):
                # Construct public download URL
                download_url = f"{protocol}://{MINIO_ENDPOINT}/api/v1/download-shared-object/{MINIO_BUCKET}/{unique_filename}"
                
                return {
                    "success": True,
                    "url": download_url,
                    "filename": unique_filename,
                    "uploaded_at": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed with status {response.status_code}: {response.text}",
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload error: {str(e)}",
        }


async def get_photo_url(filename: str) -> str:
    """
    Get the public download URL for a photo.
    
    Args:
        filename: The filename stored in MinIO
    
    Returns:
        Public URL string
    """
    protocol = "https" if MINIO_USE_SSL else "http"
    return f"{protocol}://{MINIO_ENDPOINT}/api/v1/download-shared-object/{MINIO_BUCKET}/{filename}"


async def download_photo(url: str) -> dict:
    """
    Download a photo from MinIO (for verification or processing).
    
    Args:
        url: Full MinIO download URL
    
    Returns:
        dict with:
            - success: bool
            - content: bytes (image data if successful)
            - content_type: str
            - error: str (if failed)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.content,
                    "content_type": response.headers.get("content-type", "image/jpeg"),
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed with status {response.status_code}",
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Download error: {str(e)}",
        }


__all__ = ["upload_photo", "get_photo_url", "download_photo"]
