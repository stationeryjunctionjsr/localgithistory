"""
HttpOnly cookie helpers for secure JWT token storage.

Tokens are set as HttpOnly cookies so JavaScript cannot access them,
protecting against XSS-based token theft. The backend reads tokens from
cookies (web) or Authorization header (mobile).
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
SESSION_ID_COOKIE = "session_id"

ACCESS_TOKEN_MAX_AGE = 60 * 60  # 1 hour
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
SESSION_ID_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def _is_secure() -> bool:
    """Return True for any deployed environment — only skip Secure flag for local dev."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env not in ("development", "local")


def set_auth_cookies(
    response: JSONResponse,
    access_token: str,
    refresh_token: str | None = None,
    session_id: str | None = None,
) -> JSONResponse:
    """Attach HttpOnly auth cookies to a response."""
    secure = _is_secure()
    samesite = "lax"

    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=ACCESS_TOKEN_MAX_AGE,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            REFRESH_TOKEN_COOKIE,
            refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=REFRESH_TOKEN_MAX_AGE,
            path="/api/auth",
        )
    if session_id:
        response.set_cookie(
            SESSION_ID_COOKIE,
            str(session_id),
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=SESSION_ID_MAX_AGE,
            path="/",
        )
    return response


def clear_auth_cookies(response: JSONResponse) -> JSONResponse:
    """Remove auth cookies from a response."""
    for name in (ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, SESSION_ID_COOKIE):
        response.delete_cookie(name, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/api/auth")
    return response


def get_token_from_request(request: Request) -> str | None:
    """
    Extract access token: prefer Authorization header (mobile),
    fall back to HttpOnly cookie (web).
    """
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    return request.cookies.get(ACCESS_TOKEN_COOKIE)


def get_refresh_token_from_request(request: Request) -> str | None:
    """Extract refresh token from cookie."""
    return request.cookies.get(REFRESH_TOKEN_COOKIE)
