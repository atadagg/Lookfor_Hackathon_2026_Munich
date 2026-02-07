"""Image storage for email attachments (MinIO or local fallback).

When MINIO_ACCESS_KEY and MINIO_SECRET_KEY are set, uploads go to MinIO.
Otherwise, falls back to local filesystem under ./data/uploads/ for development.
"""

from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# MinIO config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "attachments")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() in ("true", "1", "yes")

# Local fallback directory when MinIO creds are not configured
LOCAL_UPLOAD_DIR = Path("data/uploads")
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_minio_client = None


def _get_minio_client():
    """Lazy-init MinIO client. Returns None if credentials are not configured."""
    global _minio_client
    if _minio_client is not None:
        return _minio_client
    if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
        return None
    try:
        from minio import Minio

        _minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_USE_SSL,
        )
        return _minio_client
    except ImportError:
        return None


def _guess_extension(content_type: str) -> str:
    """Map content-type to file extension."""
    m = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return m.get(content_type.lower(), ".bin")


def upload_attachment(
    conversation_id: str,
    data: bytes,
    content_type: str,
    filename: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Upload attachment bytes to storage.

    Returns a dict with keys: object_key, filename, content_type, url.
    Returns None if upload fails.
    """
    ext = _guess_extension(content_type)
    safe_name = (filename or "attachment").split("/")[-1][:64]
    if not safe_name.endswith(ext):
        safe_name = f"{safe_name}{ext}" if "." not in safe_name else safe_name
    object_key = f"attachments/{conversation_id}/{uuid.uuid4().hex}{ext}"

    client = _get_minio_client()
    if client is not None:
        try:
            from io import BytesIO

            if not client.bucket_exists(MINIO_BUCKET):
                client.make_bucket(MINIO_BUCKET)
            client.put_object(
                MINIO_BUCKET,
                object_key,
                BytesIO(data),
                len(data),
                content_type=content_type,
            )
            # URL will be served via our proxy; store object_key for lookup
            return {
                "object_key": object_key,
                "filename": safe_name,
                "content_type": content_type,
            }
        except Exception as e:
            # Log but don't crash - could fall back to local
            import logging

            logging.getLogger(__name__).warning("MinIO upload failed: %s", e)
            # Fall through to local
    # Local fallback
    return _upload_local(conversation_id, data, content_type, safe_name, object_key)


def _upload_local(
    conversation_id: str,
    data: bytes,
    content_type: str,
    filename: str,
    object_key: str,
) -> Dict[str, Any]:
    """Store attachment on local filesystem."""
    parts = object_key.split("/")
    local_dir = LOCAL_UPLOAD_DIR / conversation_id
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / parts[-1]
    local_path.write_bytes(data)
    return {
        "object_key": object_key,
        "filename": filename,
        "content_type": content_type,
        "local_path": str(local_path),
    }


def get_attachment_stream(object_key: str) -> Optional[tuple[bytes, str]]:
    """Fetch attachment and return (data, content_type). Returns None if not found."""
    # Check local first (objects stored as data/uploads/{conv_id}/{filename})
    if object_key.startswith("attachments/"):
        rel = object_key[len("attachments/") :]
    else:
        rel = object_key
    local_path = LOCAL_UPLOAD_DIR / rel
    if local_path.exists():
        data = local_path.read_bytes()
        # Guess content type from extension
        ext = local_path.suffix.lower()
        ct = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(
            ext.lstrip("."), "application/octet-stream"
        )
        return (data, ct)

    client = _get_minio_client()
    if client is None:
        return None
    try:
        from io import BytesIO

        resp = client.get_object(MINIO_BUCKET, object_key)
        data = resp.read()
        content_type = getattr(resp, "headers", {}).get("Content-Type", "application/octet-stream")
        return (data, content_type)
    except Exception:
        return None
