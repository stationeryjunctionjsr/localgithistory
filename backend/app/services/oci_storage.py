"""
OCI Object Storage: upload objects and generate read access via Pre-Authenticated Requests (PAR).
Bucket is private; no binary data in DB — only object keys and PAR/signed URLs for display.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from circuitbreaker import circuit
from fastapi import HTTPException

from app.utils.retry import with_retry

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

IMAGE_MAGIC_BYTES = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
    b"RIFF": ".webp",  # WebP starts with RIFF....WEBP
    b"<svg": ".svg",
    b"\x00\x00\x01\x00": ".ico",
    b"BM": ".bmp",
}


def validate_image_content(content: bytes, filename: str) -> None:
    """Validate file content via magic bytes and enforce size + extension limits."""
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
        )

    ext = Path(filename or "").suffix.lower()
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not allowed. Accepted: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    header = content[:16]
    matched = False
    for magic, _ in IMAGE_MAGIC_BYTES.items():
        if header.startswith(magic):
            matched = True
            break
    if not matched:
        raise HTTPException(
            status_code=400,
            detail="File content does not match a supported image format",
        )


from app.config.oci import (
    OCI_BUCKET_NAME,
    OCI_FINGERPRINT,
    OCI_NAMESPACE,
    OCI_PAR_EXPIRY_SECONDS,
    OCI_PRIVATE_KEY,
    OCI_REGION,
    OCI_TENANCY_OCID,
    OCI_USER_OCID,
    use_oci_storage,
)


def _get_client():
    """Build OCI Object Storage client from config or env. Lazy to avoid import at startup."""
    try:
        import oci
    except ImportError:
        return None

    # Try environment variables first (most flexible for cloud/scripts)
    if OCI_USER_OCID and OCI_TENANCY_OCID and OCI_FINGERPRINT and OCI_PRIVATE_KEY:
        try:
            # Handle potential \n in private key from .env strings
            key_content = OCI_PRIVATE_KEY.strip()
            if "\\n" in key_content:
                key_content = key_content.replace("\\n", "\n")

            # If the user didn't include the BEGIN/END headers, wrap it (but they usually do)
            if "-----BEGIN" not in key_content:
                key_content = f"-----BEGIN RSA PRIVATE KEY-----\n{key_content}\n-----END RSA PRIVATE KEY-----"

            config = {
                "user": OCI_USER_OCID,
                "key_content": key_content,
                "fingerprint": OCI_FINGERPRINT,
                "tenancy": OCI_TENANCY_OCID,
                "region": OCI_REGION,
            }
            oci.config.validate_config(config)
            return oci.object_storage.ObjectStorageClient(config)
        except Exception as e:
            # Fall back to file config or return error later
            from app.utils.logger import logger

            logger.warning("OCI environment config validation failed, falling back to file config: %s", str(e))

    try:
        # Fall back: Prefer config file (~/.oci/config); fall back to default profile
        config = oci.config.from_file()
    except Exception as e:
        from app.utils.logger import logger

        logger.warning("OCI fallback config file load failed: %s", str(e))
        return None
    if not config:
        from app.utils.logger import logger

        logger.warning("OCI fallback config file loaded but is empty")
        return None
    return oci.object_storage.ObjectStorageClient(config)


def build_key(
    prefix: str,
    filename: str,
    *,
    entity_id: Optional[str] = None,
    subpath: str = "images",
) -> str:
    """
    Build a structured object key. Prefer entity_id when available.
    - products/{product_id}/images/{filename}
    - categories/{category_id}/images/{filename}
    - uploads/tmp/{uuid}/{filename}
    - banners/{uuid}/{filename}, etc.
    """
    from app.config.settings import settings

    env = settings.environment.lower()
    if env == "production":
        env_folder = "SJ_PROD"
    elif env == "uat":
        env_folder = "SJ_UAT"
    else:
        env_folder = "SJ_LOCAL"

    safe_name = (Path(filename).name or "file").replace("..", "").strip() or "file"
    if entity_id:
        inner_key = f"{prefix}/{entity_id}/{subpath}/{safe_name}"
    else:
        unique = uuid.uuid4().hex
        if prefix == "uploads":
            inner_key = f"uploads/tmp/{unique}/{safe_name}"
        else:
            inner_key = f"{prefix}/{unique}/{safe_name}"
    return f"{env_folder}/{inner_key}"


@circuit(failure_threshold=3, recovery_timeout=60, name="oci_upload")
@with_retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
def upload_object(key: str, data: bytes, content_type: Optional[str] = None) -> str:
    """
    Upload bytes to OCI Object Storage. Returns the object key.
    Raises if OCI is not configured or upload fails.
    Circuit opens after 3 consecutive failures and recovers after 60 s.
    """
    if not use_oci_storage():
        raise RuntimeError("OCI Object Storage is not configured")
    client = _get_client()
    if not client:
        raise RuntimeError("OCI client could not be initialized (check config)")
    put_headers = {}
    if content_type:
        put_headers["Content-Type"] = content_type
    client.put_object(
        namespace_name=OCI_NAMESPACE,
        bucket_name=OCI_BUCKET_NAME,
        object_name=key,
        put_object_body=data,
        **({"headers": put_headers} if put_headers else {}),
    )
    return key


@circuit(failure_threshold=3, recovery_timeout=60, name="oci_par")
@with_retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
def create_read_par_url(object_key: str, expiry_seconds: Optional[int] = None) -> str:
    """
    Create a Pre-Authenticated Request (PAR) for read access to one object.
    Returns the full URL that can be used in redirects or img src.
    Circuit opens after 3 consecutive failures and recovers after 60 s.
    """
    if not use_oci_storage():
        raise RuntimeError("OCI Object Storage is not configured")
    client = _get_client()
    if not client:
        raise RuntimeError("OCI client could not be initialized")
    import oci.object_storage.models as models

    expires = expiry_seconds or OCI_PAR_EXPIRY_SECONDS
    time_expires = datetime.now(timezone.utc)
    # add seconds (datetime.timedelta)
    from datetime import timedelta

    time_expires = time_expires + timedelta(seconds=expires)
    details = models.CreatePreauthenticatedRequestDetails(
        name=f"par-{uuid.uuid4().hex[:16]}",
        access_type="ObjectRead",
        object_name=object_key,
        time_expires=time_expires,
    )
    resp = client.create_preauthenticated_request(
        namespace_name=OCI_NAMESPACE,
        bucket_name=OCI_BUCKET_NAME,
        create_preauthenticated_request_details=details,
    )
    access_uri = resp.data.access_uri
    # Full PAR URL: https://objectstorage.{region}.oraclecloud.com{access_uri}
    base = f"https://objectstorage.{OCI_REGION}.oraclecloud.com"
    return f"{base}{access_uri}"


def key_to_media_path(object_key: str) -> str:
    """Turn an object key into the path the API returns (backend redirect path)."""
    from urllib.parse import quote

    return f"/api/media?key={quote(object_key, safe='')}"


def is_oci_key(value: str) -> bool:
    """True if value looks like an OCI object key (not a local /uploads path or full URL)."""
    if not value:
        return False
    v = value.strip()
    if v.startswith("http") or v.startswith("/"):
        return False
    # Keys: products/..., categories/..., uploads/tmp/..., banners/..., etc.
    return "/" in v and not v.startswith(".")


async def upload_image_and_return_path(
    file,
    prefix: str,
    *,
    entity_id: Optional[str] = None,
    filename_prefix: str = "img",
) -> str:
    """
    Upload an image (FastAPI UploadFile); returns path for API response.
    When OCI is configured: uploads to OCI and returns /api/media?key=...
    Otherwise: saves to local uploads/{prefix} and returns /uploads/{prefix}/...
    """
    import asyncio
    import random
    from datetime import datetime
    from pathlib import Path

    ext = Path((file.filename if file.filename is not None else "") or "img").suffix or ".png"
    unique = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100000000, 999999999))
    safe_filename = f"{filename_prefix}-{unique}{ext}"

    content = await file.read()
    original_filename = (file.filename if file.filename is not None else "") or "img"
    validate_image_content(content, original_filename)

    if use_oci_storage():
        key = build_key(prefix, safe_filename, entity_id=entity_id)
        content_type = file.content_type or "application/octet-stream"
        await asyncio.to_thread(upload_object, key, content, content_type)
        return key_to_media_path(key)

    # Local fallback
    from app.config.settings import settings

    env = settings.environment.lower()
    if env == "production":
        env_folder = "SJ_PROD"
    elif env == "uat":
        env_folder = "SJ_UAT"
    else:
        env_folder = "SJ_LOCAL"

    upload_dir = Path(__file__).resolve().parents[2] / "uploads" / env_folder / prefix
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    return f"/uploads/{env_folder}/{prefix}/{safe_filename}"


async def upload_base64_image_and_return_path(
    base64_str: str,
    prefix: str,
    *,
    entity_id: Optional[str] = None,
    filename_prefix: str = "img",
) -> str:
    """
    Upload a base64-encoded image; returns path for API response.
    When OCI is configured: uploads to OCI and returns /api/media?key=...
    Otherwise: saves to local uploads/{prefix} and returns /uploads/{prefix}/...
    """
    import asyncio
    import base64
    import random
    from datetime import datetime
    from pathlib import Path

    # Parse base64 string
    try:
        if "," in base64_str:
            header, base64_str = base64_str.split(",", 1)
            ext = "." + header.split("/")[1].split(";")[0]
            content_type = header.split(":")[1].split(";")[0]
        else:
            ext = ".png"
            content_type = "image/png"

        content = base64.b64decode(base64_str)
    except Exception as e:
        from app.utils.logger import logger

        logger.error(f"Error decoding base64 image: {e}")
        return base64_str

    validate_image_content(content, f"upload{ext}")

    unique = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100000000, 999999999))
    safe_filename = f"{filename_prefix}-{unique}{ext}"

    if use_oci_storage():
        key = build_key(prefix, safe_filename, entity_id=entity_id)
        await asyncio.to_thread(upload_object, key, content, content_type)
        return key_to_media_path(key)

    # Local fallback
    from app.config.settings import settings

    env = settings.environment.lower()
    if env == "production":
        env_folder = "SJ_PROD"
    elif env == "uat":
        env_folder = "SJ_UAT"
    else:
        env_folder = "SJ_LOCAL"

    upload_dir = Path(__file__).resolve().parents[2] / "uploads" / env_folder / prefix
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    return f"/uploads/{env_folder}/{prefix}/{safe_filename}"
