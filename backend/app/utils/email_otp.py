import os
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config.database import use_oracle
from app.utils.logger import logger

# Policy Settings
EMAIL_OTP_LENGTH = 6
EMAIL_OTP_VALID_SECONDS = 15 * 60  # 15 minutes
EMAIL_RESEND_COOLDOWN_SECONDS = 60  # 60s resend cooldown
EMAIL_MAX_SENDS_PER_HOUR = 5  # Max 5 sends per hour
EMAIL_SEND_WINDOW_SECONDS = 60 * 60  # 1 hour window

# In-memory fallback (used when Oracle is not configured)
email_otp_store: Dict[str, Dict[str, Any]] = {}


def generate_email_otp() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(EMAIL_OTP_LENGTH)])


def send_verification_email_sync(email: str, otp_code: str) -> bool:
    """Send verification email via EmailService"""
    try:
        from app.services.email_service import email_service

        return email_service.send_verification_email(email, otp_code)
    except Exception as e:
        logger.error(f"Failed to send email verification: {e}", exc_info=True)
        return False


# ─── Oracle DB-backed Email OTP functions ───


async def _db_request_otp(email: str, device_key: str = "default") -> Tuple[bool, Dict[str, Any]]:
    from app.db.mysql_email_otp_dao import email_otp_dao

    email_lower = email.lower()
    send_count = await email_otp_dao.count_sends_in_window(email_lower, EMAIL_SEND_WINDOW_SECONDS)
    if send_count >= EMAIL_MAX_SENDS_PER_HOUR:
        return False, {
            "message": "Maximum verification attempts reached. Please try again in 1 hour.",
            "retry_after_seconds": 3600,
        }

    existing = await email_otp_dao.find_active_otp(email_lower, device_key)

    if existing:
        last_sent = (existing["last_sent_at"] if "last_sent_at" in existing else 0)
        now = time.time()
        since_last = now - last_sent
        if since_last < EMAIL_RESEND_COOLDOWN_SECONDS:
            resend_in = int(max(1, EMAIL_RESEND_COOLDOWN_SECONDS - since_last))
            return True, {"resend_available_in_seconds": resend_in, "sent": False}

        await email_otp_dao.update_last_sent(existing["id"])
        await email_otp_dao.record_send(email_lower)

        otp_code = existing["otp"]
        sent_ok = send_verification_email_sync(email_lower, otp_code)
        if not sent_ok:
            return False, {"message": "Failed to send verification email. Please check configuration."}

        return True, {
            "otp": otp_code,
            "expires_at": existing["expires_at"],
            "resend_available_in_seconds": EMAIL_RESEND_COOLDOWN_SECONDS,
            "sent": True,
        }

    otp_code = generate_email_otp()
    record = await email_otp_dao.create_otp(email_lower, device_key, otp_code, EMAIL_OTP_VALID_SECONDS)
    await email_otp_dao.record_send(email_lower)

    sent_ok = send_verification_email_sync(email_lower, otp_code)
    if not sent_ok:
        return False, {"message": "Failed to send verification email. Please check configuration."}

    return True, {
        "otp": otp_code,
        "expires_at": record["expires_at"],
        "resend_available_in_seconds": EMAIL_RESEND_COOLDOWN_SECONDS,
        "sent": True,
    }


async def _db_verify_otp(
    email: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    from app.db.mysql_email_otp_dao import email_otp_dao

    email_lower = email.lower()
    stored = await email_otp_dao.find_active_otp(email_lower, device_key)
    if not stored:
        return {"valid": False, "message": "Verification code not found or expired."}

    if stored["verify_attempts"] >= 5:
        await email_otp_dao.delete_otp(stored["id"])
        return {"valid": False, "message": "Too many attempts. Please request a new verification code."}

    await email_otp_dao.increment_attempts(stored["id"])

    if str(stored["otp"]) == str(provided_otp).strip():
        if delete_on_success:
            await email_otp_dao.delete_otp(stored["id"])
        return {"valid": True, "message": "Email verified successfully."}

    return {"valid": False, "message": "Invalid verification code."}


# ─── In-memory fallback Email OTP functions ───


def _prune_timestamps(timestamps: List[float], *, now: float, window_seconds: float) -> List[float]:
    threshold = now - window_seconds
    return [ts for ts in timestamps if ts >= threshold]


def _get_email_record(email: str) -> Optional[Dict[str, Any]]:
    record = (email_otp_store[email.lower()] if email.lower() in email_otp_store else None)
    if not record:
        return None
    if not isinstance((record["devices"] if "devices" in record else None), dict):
        record["devices"] = {}
    send_timestamps = (record["send_timestamps"] if "send_timestamps" in record else None)
    if not isinstance(send_timestamps, list):
        record["send_timestamps"] = []
    return record


def _get_device_record(user_record: Dict[str, Any], device_key: str, *, now: float) -> Optional[Dict[str, Any]]:
    devices = user_record.setdefault("devices", {})
    device = (devices[device_key] if device_key in devices else None)
    if not device:
        return None
    expires_at = float((device["expires_at"] if "expires_at" in device else None) or 0.0)
    if now > expires_at:
        devices.pop(device_key, None)
        return None
    return device


def _mem_request_otp(email: str, device_key: str = "default") -> Tuple[bool, Dict[str, Any]]:
    email_lower = email.lower()
    now = time.time()
    user_record = _get_email_record(email_lower)
    if not user_record:
        user_record = {"send_timestamps": [], "devices": {}}
        email_otp_store[email_lower] = user_record

    send_timestamps = [float(x) for x in (user_record["send_timestamps"] if "send_timestamps" in user_record else []) if isinstance(x, (int, float))]
    send_timestamps = _prune_timestamps(send_timestamps, now=now, window_seconds=EMAIL_SEND_WINDOW_SECONDS)
    user_record["send_timestamps"] = send_timestamps

    if len(send_timestamps) >= EMAIL_MAX_SENDS_PER_HOUR:
        oldest_in_window = min(send_timestamps)
        retry_after = int(max(0, (oldest_in_window + EMAIL_SEND_WINDOW_SECONDS) - now))
        return False, {
            "message": "Maximum verification attempts reached. Please try again in 1 hour.",
            "retry_after_seconds": retry_after,
        }

    device_record = _get_device_record(user_record, device_key, now=now)

    if device_record:
        last_sent_at = float((device_record["last_sent_at"] if "last_sent_at" in device_record else None) or 0.0)
        since_last = now - last_sent_at
        if since_last < EMAIL_RESEND_COOLDOWN_SECONDS:
            resend_in = int(max(1, EMAIL_RESEND_COOLDOWN_SECONDS - since_last))
            return True, {"resend_available_in_seconds": resend_in, "sent": False}

        user_record["send_timestamps"].append(now)
        device_record["last_sent_at"] = now
        otp_code = str((device_record["otp"] if "otp" in device_record else None))
        sent_ok = send_verification_email_sync(email_lower, otp_code)
        if not sent_ok:
            return False, {"message": "Failed to send verification email. Please check configuration."}
        return True, {
            "otp": otp_code,
            "expires_at": float((device_record["expires_at"] if "expires_at" in device_record else None)),
            "resend_available_in_seconds": EMAIL_RESEND_COOLDOWN_SECONDS,
            "sent": True,
        }

    otp_code = generate_email_otp()
    expires_at = now + EMAIL_OTP_VALID_SECONDS
    user_record["send_timestamps"].append(now)
    user_record.setdefault("devices", {})[device_key] = {
        "otp": otp_code,
        "created_at": now,
        "expires_at": expires_at,
        "last_sent_at": now,
        "verify_attempts": 0,
    }
    sent_ok = send_verification_email_sync(email_lower, otp_code)
    if not sent_ok:
        return False, {"message": "Failed to send verification email. Please check configuration."}
    return True, {
        "otp": otp_code,
        "expires_at": expires_at,
        "resend_available_in_seconds": EMAIL_RESEND_COOLDOWN_SECONDS,
        "sent": True,
    }


def _mem_verify_otp(
    email: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    email_lower = email.lower()
    now = time.time()
    user_record = _get_email_record(email_lower)
    if not user_record:
        return {"valid": False, "message": "Verification code not found or expired."}
    stored = _get_device_record(user_record, device_key, now=now)
    if not stored:
        return {"valid": False, "message": "Verification code not found or expired."}

    verify_attempts = int((stored["verify_attempts"] if "verify_attempts" in stored else None) or 0)
    if verify_attempts >= 5:
        (user_record["devices"] if "devices" in user_record else {}).pop(device_key, None)
        return {"valid": False, "message": "Too many attempts. Please request a new verification code."}

    stored["verify_attempts"] = verify_attempts + 1

    if str((stored["otp"] if "otp" in stored else None)) == str(provided_otp).strip():
        if delete_on_success:
            (user_record["devices"] if "devices" in user_record else {}).pop(device_key, None)
        return {"valid": True, "message": "Email verified successfully."}

    return {"valid": False, "message": "Invalid verification code."}


# ─── Public API ───


async def request_email_otp_async(email: str, device_key: str = "default") -> Tuple[bool, Dict[str, Any]]:
    """Async request function for email OTP."""
    return await _db_request_otp(email, device_key)


async def verify_email_otp_async(
    email: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    """Async verify function for email OTP."""
    return await _db_verify_otp(email, provided_otp, device_key, delete_on_success)
