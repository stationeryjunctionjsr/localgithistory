import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# Token settings
# Access token: short-lived, sent with every API request. When expired, frontend uses refresh token to get a new one (no re-login).
# Refresh token: long-lived, used only to obtain new access tokens. User stays logged in until INACTIVITY_DAYS or login on another device.
# Intended behavior: user stays logged in on a device+browser until (1) 30 days inactivity, or (2) they log in on another device (other sessions revoked).
from app.config.settings import settings

SECRET_KEY = settings.jwt_secret_key or os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required. Set it in your .env file.")

REFRESH_SECRET_KEY = settings.jwt_refresh_secret_key or os.getenv("JWT_REFRESH_SECRET_KEY") or SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour; frontend refreshes automatically via refresh token when this expires
REFRESH_TOKEN_EXPIRE_DAYS = 30
INACTIVITY_DAYS = 30  # session revoked after this many days without any request; user must log in again

# Error codes
ERR_SESSION_REVOKED = "SESSION_REVOKED"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using bcrypt directly"""
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.warning("Password verification error: %s", str(e))
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(user_id: str, session_id: str) -> str:
    """Create short-lived access token tied to session"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"userId": user_id, "sessionId": session_id, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, session_id: str, refresh_id: str) -> str:
    """Create long-lived refresh token with jti"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "userId": user_id,
        "sessionId": session_id,
        "refreshId": refresh_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        if not payload.get("userId") or not payload.get("sessionId") or not payload.get("refreshId"):
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


async def verify_token(token: str) -> dict:
    """Verify JWT access token, ensure session is active, enforce inactivity window"""
    from app.repositories.session_repository import session_repository
    from app.repositories.user_repository import user_repository

    base_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise base_exception
        user_id: str = payload.get("userId")
        session_id: str = payload.get("sessionId")
        if user_id is None or session_id is None:
            raise base_exception
    except JWTError:
        raise base_exception

    session = await session_repository.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    # Inactivity check
    session = await session_repository.check_inactivity_and_revoke(session, INACTIVITY_DAYS)

    if session.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ERR_SESSION_REVOKED,
                "revokedAt": session.get("revokedAt"),
                "reason": session.get("revokedReason"),
            },
        )

    await session_repository.touch_last_active(session_id)

    user = await user_repository.findById(user_id)
    if user is None or not user.get("isActive", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    user_copy = dict(user)
    user_copy.pop("password", None)
    if user_copy.get("isDeactivated") and user_copy.get("role") == "wholesaler":
        user_copy["effectiveRole"] = "customer"
    else:
        user_copy["effectiveRole"] = user_copy.get("role", "customer")

    user_copy["sessionId"] = session_id
    return user_copy


def check_roles(user: dict, *allowed_roles: str):
    """Check if user has required role"""
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Insufficient permissions.")
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    Usage: current_user: dict = Depends(require_roles('super_admin', 'admin'))
    """
    _role_security = HTTPBearer(auto_error=False)

    async def role_checker(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_role_security),
    ):
        token = _extract_token(request, credentials)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        current_user = await verify_token(token)
        return check_roles(current_user, *allowed_roles)

    return role_checker


# Common authentication dependencies for routers
_security = HTTPBearer(auto_error=False)


def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    """Extract token from Bearer header or HttpOnly cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    from app.utils.cookies import get_token_from_request

    return get_token_from_request(request)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> dict:
    """
    Get current authenticated user from JWT token.
    Reads from Authorization header first, then HttpOnly cookie.
    Usage: current_user: dict = Depends(get_current_user)
    """
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await verify_token(token)


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> Optional[dict]:
    """
    Get current user if token provided, otherwise return None.
    """
    token = _extract_token(request, credentials)
    if not token:
        return None
    try:
        return await verify_token(token)
    except Exception as e:
        logger.warning("Optional auth token verification failed: %s", str(e))
        return None


async def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require super_admin role.
    Usage: current_user: dict = Depends(require_super_admin)
    """
    try:
        return check_roles(current_user, "super_admin")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied. Super admin only.")


async def require_super_admin_or_valet(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require super_admin or valet role.
    Usage: current_user: dict = Depends(require_super_admin_or_valet)
    """
    try:
        return check_roles(current_user, "super_admin", "valet")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied. Super admin or valet only.")
