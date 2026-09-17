"""
Serves read access to OCI Object Storage objects via redirect to a PAR URL.
Private bucket: client requests /api/media?key=... and is redirected to a short-lived PAR.
No API or response shape change; frontend keeps using the same URL pattern.
"""

from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config.oci import use_oci_storage
from app.services.oci_storage import create_read_par_url, is_oci_key
from app.utils.auth import get_current_user, get_optional_user
from app.utils.logger import logger

router = APIRouter()

# How long (seconds) the browser/CDN is allowed to cache the redirect to the PAR URL.
# OCI PAR expiry is configured via OCI_PAR_EXPIRY_SECONDS (default: typically 1h).
# We conservatively tell the browser to cache for 45 minutes so the PAR is still
# valid when the browser uses the cached redirect.
_MEDIA_CACHE_SECONDS = 45 * 60  # 45 minutes

# Allowed top-level environment prefixes — keys must start with one of these.
# This prevents an attacker from requesting arbitrary OCI keys via the redirect.
_ALLOWED_ENV_PREFIXES = ("SJ_PROD/", "SJ_UAT/", "SJ_LOCAL/")

# Key sub-paths that contain sensitive documents and require an authenticated user.
# Product/category/brand images are public; invoices and payment proofs are not.
_SENSITIVE_SUBPATHS = ("/invoices/", "/payments/")


def _is_sensitive_key(key: str) -> bool:
    """Return True if the object key points to a sensitive document."""
    return any(sub in key for sub in _SENSITIVE_SUBPATHS)


@router.get("/media", response_class=RedirectResponse)
async def get_media_url(
    key: str = Query(..., description="Object key in OCI bucket"),
    current_user=Depends(get_optional_user),
):
    """
    Redirect to a time-limited PAR URL for the given object key.
    Used for img src etc.; one round-trip: backend → 302 → OCI.
    The redirect itself is cached by the browser for 45 minutes so
    subsequent image loads skip the backend entirely.

    Public keys (product images, banners, etc.) are served without auth.
    Sensitive keys (invoices, payment proofs) require a logged-in user.
    """
    if not key:
        raise HTTPException(status_code=400, detail="key is required")
    key = unquote(key.strip())
    if not use_oci_storage():
        raise HTTPException(status_code=503, detail="Object Storage not configured")
    if not is_oci_key(key):
        raise HTTPException(status_code=400, detail="Invalid object key")

    # Enforce env-prefix allowlist — reject keys that don't belong to this deployment.
    if not any(key.startswith(p) for p in _ALLOWED_ENV_PREFIXES):
        raise HTTPException(status_code=400, detail="Invalid object key")

    # Require authentication for sensitive documents.
    if _is_sensitive_key(key) and current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        import asyncio

        par_url = await asyncio.to_thread(create_read_par_url, key)
        response = RedirectResponse(url=par_url, status_code=302)
        if _is_sensitive_key(key):
            # Don't cache sensitive redirects in shared/public caches.
            response.headers["Cache-Control"] = "private, no-store"
        else:
            response.headers["Cache-Control"] = f"public, max-age={_MEDIA_CACHE_SECONDS}, stale-while-revalidate=300"
        response.headers["Vary"] = "Accept-Encoding"
        return response
    except Exception as e:
        logger.error("Failed to generate access URL: %s", str(e), exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to generate access URL")

