from app.models.schemas import MessageResponse, CheckPhoneResponse, VerifyOtpResponse, Msg91WebhookResponse, VerifyMsg91TokenResponse
import os
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.repositories.session_repository import session_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import (
    ERR_SESSION_REVOKED,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_token,
)
from app.utils.cookies import clear_auth_cookies, get_refresh_token_from_request, set_auth_cookies
from app.utils.device import parse_device

# Initialize Limiter for auth routes (depends on main app state)
from app.utils.limiter import limiter
from app.utils.logger import logger
from app.utils.otp import (
    extract_phone_from_msg91_payload,
    normalize_phone,
    request_otp_async,
    verify_msg91_widget_token,
    verify_otp_async,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    from app.utils.cookies import get_token_from_request

    token = credentials.credentials if credentials else None
    if not token:
        token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await verify_token(token)


class SendOTPRequest(BaseModel):
    phone: str
    purpose: Optional[str] = None
    deviceId: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    deviceId: Optional[str] = None


class CheckPhoneRequest(BaseModel):
    phone: str


class VerifyMsg91Request(BaseModel):
    token: str
    phone: Optional[str] = None


@router.post("/check-phone", response_model=CheckPhoneResponse)
@limiter.limit("10/minute")
async def check_phone(data: CheckPhoneRequest, request: Request):
    """Check if a phone number or email belongs to a registered user with a real password."""
    import re
    identifier = data.phone.strip()
    is_email = "@" in identifier

    user = None
    if is_email:
        normalized_email = identifier.lower()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", normalized_email):
            raise HTTPException(status_code=400, detail="Enter a valid email address")
        user = await user_repository.findByEmail(normalized_email)
    else:
        normalized_phone = normalize_phone(identifier)
        if not normalized_phone or len(normalized_phone) != 10:
            raise HTTPException(status_code=400, detail="Enter a valid 10-digit phone number or email")
        user = await user_repository.findByPhone(normalized_phone)

    exists = bool(user and user.password)
    import hashlib
    import asyncio

    await asyncio.sleep(0.05 + (int(hashlib.sha256(identifier.encode()).hexdigest()[:4], 16) % 50) / 1000)
    return {"exists": exists}


@router.post("/send-otp", response_model=MessageResponse)
@limiter.limit("5/minute")
async def send_otp(data: SendOTPRequest, request: Request):
    try:
        normalized_phone = normalize_phone(data.phone)
        if not normalized_phone or len(normalized_phone) != 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid 10-digit phone number")
        device_key = (data.deviceId or "default").strip() or "default"

        # For registration, check if user already exists
        if data.purpose == "register":
            user = await user_repository.findByPhone(normalized_phone)
            if user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account already exists with this phone number. Please login instead.",
                )

        # For forgot password, check if user exists
        elif data.purpose == "forgot_password":
            user = await user_repository.findByPhone(normalized_phone)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="No account found with this phone number."
                )

        ok, payload = await request_otp_async(normalized_phone, device_key)
        if not ok:
            # Enforce per-user hourly send rate limit (across devices)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=payload.get("message", "Too many requests"),
                headers={"Retry-After": str(int(payload.get("retry_after_seconds") or 0))},
            )
        otp = payload.get("otp")

        # Log OTP for development/testing
        if otp:
            logger.info(f"OTP sent for {normalized_phone}")

        # In production, send SMS here
        # For development, return OTP in response
        import os

        response_data = {"message": "OTP processed"}
        if os.getenv("ENVIRONMENT") == "development" and otp:
            logger.debug(f"Dev Mode: Returning OTP {otp} in response")
            response_data["otp"] = otp
        # Let frontend manage resend button timing without erroring early calls
        response_data["resendAvailableInSeconds"] = int(payload.get("resend_available_in_seconds") or 0)
        response_data["sent"] = bool(payload.get("sent", True))

        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_otp: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/verify-otp", response_model=VerifyOtpResponse)
@limiter.limit("5/minute")
async def verify_otp_endpoint(data: VerifyOTPRequest, request: Request):
    try:
        normalized_phone = normalize_phone(data.phone)
        if not normalized_phone or len(normalized_phone) != 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid 10-digit phone number")

        device_key = (data.deviceId or "default").strip() or "default"
        logger.info(f"[VERIFY-OTP] phone=***{normalized_phone[-4:]} device_key={device_key}")
        result = await verify_otp_async(normalized_phone, data.otp, device_key=device_key, delete_on_success=False)
        logger.info(f"[VERIFY-OTP] result={result}")
        if not result["valid"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return {"message": "OTP verified successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/msg91-webhook", response_model=Msg91WebhookResponse)
async def msg91_webhook(request: Request, x_msg91_secret: Optional[str] = Header(None, alias="X-MSG91-Secret")):
    expected_secret = os.getenv("MSG91_WEBHOOK_SECRET")
    if not expected_secret:
        logger.error("MSG91_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=503, detail="Webhook not configured")
    if x_msg91_secret != expected_secret:
        logger.warning("Unauthorized webhook attempt. Secret mismatch.")
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        payload = await request.json()
        # Avoid logging full payload (may contain phone / PII); log shape only.
        status_val = None
        keys_summary = "non-dict"
        if isinstance(payload, dict):
            status_val = payload.get("Status") or payload.get("status") or payload.get("type")
            keys_summary = ",".join(sorted(payload.keys()))
        logger.info("[MSG91 WEBHOOK] OTP status update keys=%s status=%s", keys_summary, status_val)
        # Add your database logging here if needed!
        return {"status": "success", "message": "Webhook received"}
    except Exception as e:
        logger.error(f"Error processing MSG91 webhook: {e}")
        return {"status": "error", "message": "Webhook processing error"}


@router.post("/verify-msg91-token", response_model=VerifyMsg91TokenResponse)
@limiter.limit("10/minute")
async def verify_msg91_token_endpoint(data: VerifyMsg91Request, request: Request):
    """Verify a token directly from the MSG91 Widget/SDK."""
    try:
        ok, res_data = verify_msg91_widget_token(data.token)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=res_data.get("message", "Token verification failed")
            )
        if data.phone:
            normalized_phone = normalize_phone(data.phone)
            verified_phone = extract_phone_from_msg91_payload(res_data)
            if not verified_phone or verified_phone != normalized_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verified phone number does not match the submitted phone number",
                )
        return {"message": "Verified successfully", "data": res_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_msg91_token_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(user_data: RegisterRequest, request: Request):
    try:
        normalized_phone = normalize_phone(user_data.phone)
        logger.info(
            f"[REGISTER] phone=***{normalized_phone[-4:] if normalized_phone else '??'} has_msg91Token={bool(user_data.msg91Token)} "
            f"has_otp={bool(user_data.otp)} deviceId={user_data.deviceId}"
        )
        if not normalized_phone or len(normalized_phone) != 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid 10-digit phone number")

        # Always create as customer
        user_dict = user_data.dict()
        user_dict["role"] = "customer"
        user_dict["approvalStatus"] = "approved"
        user_dict["phone"] = normalized_phone
        user_dict.pop("otp", None)
        user_dict.pop("deviceId", None)

        # Check if user already exists as guest
        user = await user_repository.findByPhone(normalized_phone)
        if user:
            logger.info(f"[REGISTER] User already exists for phone=***{normalized_phone[-4:]}")
            raise HTTPException(status_code=400, detail="User with this phone number already exists")

        if user_data.msg91Token:
            logger.info(f"[REGISTER] Verifying via MSG91 token")
            ok, res_data = verify_msg91_widget_token(user_data.msg91Token)
            if not ok:
                logger.warning(f"[REGISTER] MSG91 token verification failed: {res_data}")
                raise HTTPException(status_code=400, detail="Invalid verification token")
            verified_phone = extract_phone_from_msg91_payload(res_data)
            if not verified_phone or verified_phone != normalized_phone:
                logger.warning(f"[REGISTER] Phone mismatch: verified=***{(verified_phone or '')[-4:]} expected=***{normalized_phone[-4:]}")
                raise HTTPException(
                    status_code=400,
                    detail="Verified phone number does not match the submitted phone number",
                )
        else:
            if not user_data.otp:
                logger.warning(f"[REGISTER] No OTP and no msg91Token provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone verification is required before registration",
                )
            device_key = (user_data.deviceId or "default").strip() or "default"
            logger.info(
                f"[REGISTER] Verifying OTP in DB: phone=***{normalized_phone[-4:]} device_key={device_key}"
            )
            otp_result = await verify_otp_async(
                normalized_phone, user_data.otp, device_key=device_key, delete_on_success=False
            )
            logger.info(f"[REGISTER] OTP verify result: valid={otp_result.get('valid')}")
            if not otp_result.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=otp_result.get("message", "Invalid or expired OTP"),
                )

        user = await user_repository.create(user_dict)

        # Only delete the OTP after the user is successfully created in the DB
        if not user_data.msg91Token:
            await verify_otp_async(normalized_phone, user_data.otp, device_key=device_key, delete_on_success=True)
        # Create session and tokens
        device = parse_device(request, default_type="web")
        refresh_id = str(uuid4())
        session = await session_repository.create_session(user["_id"], device, refresh_id)

        access_token = create_access_token(user["_id"], session["_id"])
        refresh_token = create_refresh_token(user["_id"], session["_id"], refresh_id)

        user_response = UserResponse(**user)

        auth_data = AuthResponse(
            token=access_token,
            refreshToken=refresh_token,
            sessionId=session["_id"],
            user=user_response,
            message="Registration successful.",
        )
        response = JSONResponse(content=auth_data.dict(), status_code=201)
        set_auth_cookies(response, access_token, refresh_token, session["_id"])
        return response
    except HTTPException as he:
        logger.warning(f"[REGISTER] HTTPException: status={he.status_code} detail={he.detail}")
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(login_data: LoginRequest, request: Request):
    # Validate password
    if not login_data.password or not login_data.password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    user = None
    if login_data.email:
        normalized_email = login_data.email.strip().lower()
        user = await user_repository.findByEmail(normalized_email)
    elif login_data.phone:
        normalized_phone = normalize_phone(login_data.phone)
        user = await user_repository.findByPhone(normalized_phone)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either email or phone must be provided")

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_match = user_repository.compare_password(user, login_data.password.strip())
    if not password_match:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not (user.is_active if user.is_active is not None else True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

    # Check approval status for wholesaler
    if user.role == "wholesaler":
        if user.approval_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending approval by Super Admin. Please wait for approval.",
                headers={"X-Approval-Status": (user.approval_status if user.approval_status is not None else "pending")},
            )

    device = parse_device(request, default_type="web")
    refresh_id = str(uuid4())
    # create session
    session = await session_repository.create_session(user["_id"], device, refresh_id)
    # revoke other sessions is disabled to allow signing into and remaining active on multiple devices
    # await session_repository.revoke_other_sessions(user["_id"], exclude_session_id=session["_id"])

    access_token = create_access_token(user["_id"], session["_id"])
    refresh_token = create_refresh_token(user["_id"], session["_id"], refresh_id)
    # Calculate effective role
    effective_role = "customer"
    if user.is_deactivated and user.role == "wholesaler":
        effective_role = "customer"
    else:
        effective_role = (user.role if user.role is not None else "customer")

    user_response_dict = {**user, "effectiveRole": effective_role}
    user_response = UserResponse(**user_response_dict)

    auth_data = AuthResponse(
        token=access_token, refreshToken=refresh_token, sessionId=session["_id"], user=user_response
    )
    response = JSONResponse(content=auth_data.dict())
    set_auth_cookies(response, access_token, refresh_token, session["_id"])
    return response


class RefreshRequest(BaseModel):
    refreshToken: Optional[str] = None


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(payload: RefreshRequest, request: Request):
    token_str = payload.refreshToken or get_refresh_token_from_request(request)
    if not token_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")
    data = verify_refresh_token(token_str)
    user_id = data.get("userId")
    session_id = data.get("sessionId")
    refresh_id = data.get("refreshId")

    session = await session_repository.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    from app.utils.auth import INACTIVITY_DAYS

    session = await session_repository.check_inactivity_and_revoke(session, INACTIVITY_DAYS)
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ERR_SESSION_REVOKED,
                "revokedAt": session.revoked_at,
                "reason": session.revoked_reason,
            },
        )

    if session.refresh_token_id != refresh_id:
        # refresh token mismatched -> revoke
        session = await session_repository.revoke_session(session_id, "refresh_mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ERR_SESSION_REVOKED,
                "revokedAt": session.revoked_at,
                "reason": session.revoked_reason,
            },
        )

    # touch activity and issue new tokens
    await session_repository.touch_last_active(session_id)
    device = parse_device(request, default_type="web")
    await session_repository.update_session(session_id, {"device": device})

    access_token = create_access_token(user_id, session_id)
    new_refresh_id = str(uuid4())
    await session_repository.update_session(session_id, {"refreshTokenId": new_refresh_id})
    refresh_token = create_refresh_token(user_id, session_id, new_refresh_id)

    user = await user_repository.findById(user_id)
    if not user or not (user.is_active if user.is_active is not None else True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Calculate effective role
    effective_role = "customer"
    if user.is_deactivated and user.role == "wholesaler":
        effective_role = "customer"
    else:
        effective_role = (user.role if user.role is not None else "customer")

    user_copy = dict(user)
    user_copy.pop("password", None)
    user_response_dict = {**user_copy, "effectiveRole": effective_role}
    user_response = UserResponse(**user_response_dict)
    auth_data = AuthResponse(token=access_token, refreshToken=refresh_token, sessionId=session_id, user=user_response)
    response = JSONResponse(content=auth_data.dict())
    set_auth_cookies(response, access_token, refresh_token, session_id)
    return response


class LogoutRequest(BaseModel):
    sessionId: Optional[str] = None


@router.post("/logout", response_model=MessageResponse)
async def logout(request: LogoutRequest, current_user: dict = Depends(get_current_user)):
    session_id = request.sessionId or current_user.session_id
    if session_id:
        await session_repository.revoke_session(session_id, "logout")
    response = JSONResponse(content={"message": "Logged out"})
    clear_auth_cookies(response)
    return response


class ForgotPasswordRequest(BaseModel):
    phone: str
    newPassword: str
    otp: str
    deviceId: Optional[str] = None
    msg91Token: Optional[str] = None


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(data: ForgotPasswordRequest, request: Request):
    try:
        # Verify OTP
        normalized_phone = normalize_phone(data.phone)
        if not normalized_phone or len(normalized_phone) != 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid 10-digit phone number")
        if data.msg91Token:
            ok, res_data = verify_msg91_widget_token(data.msg91Token)
            if not ok:
                raise HTTPException(status_code=400, detail="Invalid verification token")
        else:
            device_key = (data.deviceId or "default").strip() or "default"
            otp_result = await verify_otp_async(normalized_phone, data.otp, device_key=device_key)
            if not otp_result.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=otp_result.get("message", "Invalid or expired OTP")
                )

        # Find user by phone
        user = await user_repository.findByPhone(normalized_phone)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found with this phone number")

        # Update password (UserRepository.update will handle hashing)
        await user_repository.update(user["_id"], {"password": data.newPassword})

        return {"message": "Password reset successful"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")


@router.delete("/me", status_code=200, response_model=MessageResponse)
async def delete_own_account(current_user: dict = Depends(get_current_user)):
    """GDPR / DPDP right-to-erasure: authenticated user permanently deletes their own account.

    All active sessions are revoked before deletion so any in-flight tokens
    immediately become invalid.
    """
    user_id = current_user.id or current_user.id
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify user from token")

    # Revoke current session so the token cannot be reused after deletion
    session_id = current_user.session_id
    if session_id:
        try:
            await session_repository.revoke_session(session_id, "self_deletion")
        except Exception as exc:
            logger.warning("Session revoke failed during self-deletion of user %s: %s", user_id, exc)

    try:
        await user_repository.delete(user_id)
    except Exception as exc:
        logger.error("Error deleting user account %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete account. Please try again.") from exc

    logger.info("User account self-deleted: %s", user_id)
    response = JSONResponse(content={"message": "Your account and data have been permanently deleted."})
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    # Calculate effective role
    effective_role = "customer"
    if current_user.is_deactivated and current_user.role == "wholesaler":
        effective_role = "customer"
    else:
        effective_role = (current_user.role if current_user.role is not None else "customer")

    user_response_dict = {**current_user, "effectiveRole": effective_role}
    return UserResponse(**user_response_dict)
