"""
Serves read access to OCI Object Storage objects via redirect to a PAR URL.
Private bucket: client requests /api/media?key=... and is redirected to a short-lived PAR.
No API or response shape change; frontend keeps using the same URL pattern.
"""

from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config.oci import use_oci_storage
from app.services.oci_storage import create_read_par_url, is_oci_key
from app.utils.logger import logger

router = APIRouter()

# How long (seconds) the browser/CDN is allowed to cache the redirect to the PAR URL.
# OCI PAR expiry is configured via OCI_PAR_EXPIRY_SECONDS (default: typically 1h).
# We conservatively tell the browser to cache for 45 minutes so the PAR is still
# valid when the browser uses the cached redirect.
_MEDIA_CACHE_SECONDS = 45 * 60  # 45 minutes


@router.get("/media", response_class=RedirectResponse)
async def get_media_url(key: str = Query(..., description="Object key in OCI bucket")):
    """
    Redirect to a time-limited PAR URL for the given object key.
    Used for img src etc.; one round-trip: backend → 302 → OCI.
    The redirect itself is cached by the browser for 45 minutes so
    subsequent image loads skip the backend entirely.
    """
    if not key:
        raise HTTPException(status_code=400, detail="key is required")
    key = unquote(key.strip())
    if not use_oci_storage():
        raise HTTPException(status_code=503, detail="Object Storage not configured")
    if not is_oci_key(key):
        raise HTTPException(status_code=400, detail="Invalid object key")
    try:
        import asyncio

        par_url = await asyncio.to_thread(create_read_par_url, key)
        response = RedirectResponse(url=par_url, status_code=302)
        response.headers["Cache-Control"] = f"public, max-age={_MEDIA_CACHE_SECONDS}, stale-while-revalidate=300"
        response.headers["Vary"] = "Accept-Encoding"
        return response
    except Exception as e:
        logger.error("Failed to generate access URL: %s", str(e), exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to generate access URL")
