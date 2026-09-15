import os
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
import requests.exceptions

from app.config.database import use_oracle
from app.utils.logger import logger
from app.utils.retry import with_retry

# Policy
OTP_LENGTH = 6
OTP_VALID_SECONDS = 15 * 60
RESEND_COOLDOWN_SECONDS = 30
MAX_SENDS_PER_HOUR = 50
SEND_WINDOW_SECONDS = 60 * 60

# In-memory fallback (used when Oracle is not configured)
otp_store: Dict[str, Dict[str, Any]] = {}


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def normalize_phone(phone: str) -> str:
    """Standardize phone number to 10 digits without prefix."""
    clean = "".join(filter(str.isdigit, phone))
    if len(clean) == 11 and clean.startswith("0"):
        clean = clean[1:]
    elif len(clean) == 12 and clean.startswith("91"):
        clean = clean[2:]
    if len(clean) > 10:
        clean = clean[-10:]
    return clean


@with_retry(
    max_attempts=3,
    initial_delay=0.5,
    backoff_factor=2.0,
    exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout),
)
def send_otp_via_sms(phone: str, otp: str) -> bool:
    """Send OTP via configured SMS provider (MSG91 / Fast2SMS / 2Factor.in)"""
    provider = os.getenv("SMS_PROVIDER", "msg91")

    if os.getenv("ENVIRONMENT") == "development" and not os.getenv("FORCE_SMS"):
        logger.info(f"[DEV] Mocking SMS send to ***{normalize_phone(phone)[-4:]}")
        return True

    target_phone = f"91{normalize_phone(phone)}"

    try:
        if provider == "msg91":
            api_key = os.getenv("MSG91_AUTH_KEY")
            widget_id = os.getenv("MSG91_WIDGET_ID")
            if not api_key or not widget_id:
                logger.error("MSG91_AUTH_KEY or MSG91_WIDGET_ID not found")
                return False
            url = "https://control.msg91.com/api/v5/widget/sendOtp"
            try:
                payload = {"authkey": api_key, "identifier": target_phone, "widgetId": widget_id, "otp": otp}
                response = requests.post(url, json=payload, timeout=10)
                res_data = response.json()
                if (
                    (res_data["type"] if "type" in res_data else None) == "success"
                    or (res_data["message"] if "message" in res_data else None) == "success"
                    or (res_data["status"] if "status" in res_data else None) == "success"
                ):
                    logger.info(f"OTP sent via MSG91 to ***{target_phone[-4:]}")
                    return True
                else:
                    logger.error(f"MSG91 Send Error: {res_data}")
                    return False
            except Exception as e:
                logger.error(f"MSG91 Send failed: {e}")
                return False

        elif provider == "2factor":
            api_key = os.getenv("OTP_API_KEY")
            if not api_key:
                return False
            url = f"https://2factor.in/API/V1/{api_key}/SMS/{target_phone}/{otp}"
            response = requests.get(url, timeout=10)
            return (response.json()["Status"] if "Status" in response.json() else None) == "Success"

        elif provider == "fast2sms":
            api_key = os.getenv("OTP_API_KEY")
            if not api_key:
                return False
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {"authorization": api_key, "Content-Type": "application/x-www-form-urlencoded"}
            payload_data = {"variables_values": otp, "route": "otp", "numbers": normalize_phone(phone)}
            response = requests.post(url, data=payload_data, headers=headers, timeout=10)
            return (response.json()["return"] if "return" in response.json() else None) is True

        return False
    except Exception as e:
        logger.error(f"Error sending SMS via {provider}: {e}")
        return False


def verify_msg91_widget_token(token: str) -> Tuple[bool, Dict[str, Any]]:
    """Verify a MSG91 Widget Access Token (JWT) with MSG91 server"""
    api_key = os.getenv("MSG91_AUTH_KEY")
    if not api_key:
        logger.error("MSG91_AUTH_KEY not found in environment")
        return False, {"message": "Server configuration error"}
    url = "https://control.msg91.com/api/v5/widget/verifyAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"authkey": api_key, "access-token": token}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        if response.status_code == 200 and (res_data["status"] if "status" in res_data else None) != "error":
            logger.info("MSG91 Widget Token verified successfully")
            return True, res_data
        else:
            logger.error(f"MSG91 Token verification failed: {res_data}")
            return False, {"message": (res_data["message"] if "message" in res_data else None) or "Verification failed"}
    except Exception as e:
        logger.error(f"Error verifying MSG91 token: {e}")
        return False, {"message": "Internal verification error"}


def extract_phone_from_msg91_payload(payload: Any) -> Optional[str]:
    """Best-effort extraction of the verified phone number from MSG91 payloads."""

    def _walk(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            prioritized_keys = (
                "mobile",
                "phone",
                "phoneNumber",
                "phone_number",
                "identifier",
                "value",
            )
            for key in prioritized_keys:
                candidate = (value[key] if key in value else None)
                if isinstance(candidate, str):
                    normalized = normalize_phone(candidate)
                    if len(normalized) == 10:
                        return normalized
            for nested in value.values():
                found = _walk(nested)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = _walk(item)
                if found:
                    return found
        elif isinstance(value, str):
            normalized = normalize_phone(value)
            if len(normalized) == 10:
                return normalized
        return None

    return _walk(payload)


def verify_otp_via_msg91_headless(phone: str, otp: str) -> Tuple[bool, Dict[str, Any]]:
    """Verify a raw 4-6 digit OTP with MSG91 Headless API (fallback)"""
    api_key = os.getenv("MSG91_AUTH_KEY")
    widget_id = os.getenv("MSG91_WIDGET_ID")
    if not api_key or not widget_id:
        return False, {"message": "Server configuration error"}
    target_phone = f"91{normalize_phone(phone)}"
    url = "https://control.msg91.com/api/v5/widget/verifyOtp"
    try:
        response = requests.post(
            url,
            json={"authkey": api_key, "mobile": target_phone, "otp": otp, "widgetId": widget_id},
            timeout=10,
        )
        res_data = response.json()
        if (res_data["status"] if "status" in res_data else None) == "success":
            logger.info(f"OTP verified via MSG91 Headless API for ***{target_phone[-4:]}")
            return True, res_data
        else:
            logger.error(f"MSG91 Headless Verify Error: {res_data}")
            return False, {"message": (res_data["message"] if "message" in res_data else None) or "Invalid OTP"}
    except Exception as e:
        logger.error(f"Error in MSG91 manual verify: {e}")
        return False, {"message": "Verification error"}


# ─── Oracle DB-backed OTP functions ───


async def _db_request_otp(user_key: str, device_key: str) -> Tuple[bool, Dict[str, Any]]:
    from app.db.mysql_otp_dao import otp_dao

    send_count = await otp_dao.count_sends_in_window(user_key, SEND_WINDOW_SECONDS)
    if send_count >= MAX_SENDS_PER_HOUR:
        return False, {"message": "Maximum attempts reached. Retry after 1 hour.", "retry_after_seconds": 3600}

    existing = await otp_dao.find_active_otp(user_key, device_key)

    if existing:
        last_sent = (existing["last_sent_at"] if "last_sent_at" in existing else 0)
        now = time.time()
        since_last = now - last_sent
        if since_last < RESEND_COOLDOWN_SECONDS:
            resend_in = int(max(1, RESEND_COOLDOWN_SECONDS - since_last))
            return True, {"resend_available_in_seconds": resend_in, "sent": False}

        await otp_dao.update_last_sent(existing["id"])
        await otp_dao.record_send(user_key)

        otp_code = existing["otp"]
        sent_ok = send_otp_via_sms(user_key, otp_code)
        if not sent_ok:
            return False, {"message": "Failed to send SMS. Please check provider configuration."}

        return True, {
            "otp": otp_code,
            "expires_at": existing["expires_at"],
            "resend_available_in_seconds": 0,
            "sent": True,
        }

    otp_code = generate_otp()
    record = await otp_dao.create_otp(user_key, device_key, otp_code, OTP_VALID_SECONDS)
    await otp_dao.record_send(user_key)

    sent_ok = send_otp_via_sms(user_key, otp_code)
    if not sent_ok:
        return False, {"message": "Failed to send SMS. Please check provider configuration."}

    return True, {
        "otp": otp_code,
        "expires_at": record["expires_at"],
        "resend_available_in_seconds": 0,
        "sent": True,
    }


async def _db_verify_otp(
    user_key: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    from app.db.mysql_otp_dao import otp_dao

    stored = await otp_dao.find_active_otp(user_key, device_key)
    if not stored:
        return {"valid": False, "message": "OTP not found or expired"}

    await otp_dao.increment_attempts(stored["id"])

    if stored["verify_attempts"] + 1 >= 5:
        await otp_dao.delete_otp(stored["id"])
        return {"valid": False, "message": "Too many attempts. Please request a new OTP"}

    if str(stored["otp"]) == str(provided_otp):
        if delete_on_success:
            await otp_dao.delete_otp(stored["id"])
        return {"valid": True, "message": "OTP verified"}

    provider = os.getenv("SMS_PROVIDER", "msg91")
    is_dev = os.getenv("ENVIRONMENT") == "development" and not os.getenv("FORCE_SMS")
    if provider == "msg91" and not is_dev:
        ok, res_data = verify_otp_via_msg91_headless(user_key, provided_otp)
        if ok:
            if delete_on_success:
                await otp_dao.delete_otp(stored["id"])
            return {"valid": True, "message": "OTP verified"}
        else:
            return {"valid": False, "message": (res_data["message"] if "message" in res_data else None) or "Invalid OTP"}

    return {"valid": False, "message": "Invalid OTP"}


# ─── In-memory fallback OTP functions (no DB) ───


def _prune_timestamps(timestamps: List[float], *, now: float, window_seconds: float) -> List[float]:
    threshold = now - window_seconds
    return [ts for ts in timestamps if ts >= threshold]


def _get_user_record(user_key: str) -> Optional[Dict[str, Any]]:
    record = otp_store[user_key] if user_key in otp_store else None
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


def _mem_request_otp(user_key: str, device_key: str) -> Tuple[bool, Dict[str, Any]]:
    now = time.time()
    user_record = _get_user_record(user_key)
    if not user_record:
        user_record = {"send_timestamps": [], "devices": {}}
        otp_store[user_key] = user_record

    send_timestamps = [float(x) for x in (user_record["send_timestamps"] if "send_timestamps" in user_record else []) if isinstance(x, (int, float))]
    send_timestamps = _prune_timestamps(send_timestamps, now=now, window_seconds=SEND_WINDOW_SECONDS)
    user_record["send_timestamps"] = send_timestamps

    if len(send_timestamps) >= MAX_SENDS_PER_HOUR:
        oldest_in_window = min(send_timestamps)
        retry_after = int(max(0, (oldest_in_window + SEND_WINDOW_SECONDS) - now))
        return False, {"message": "Maximum attempts reached. Retry after 1 hour.", "retry_after_seconds": retry_after}

    device_record = _get_device_record(user_record, device_key, now=now)

    if device_record:
        last_sent_at = float((device_record["last_sent_at"] if "last_sent_at" in device_record else None) or 0.0)
        since_last = now - last_sent_at
        if since_last < RESEND_COOLDOWN_SECONDS:
            resend_in = int(max(1, RESEND_COOLDOWN_SECONDS - since_last))
            return True, {"resend_available_in_seconds": resend_in, "sent": False}

        user_record["send_timestamps"].append(now)
        device_record["last_sent_at"] = now
        otp_code = str((device_record["otp"] if "otp" in device_record else None))
        sent_ok = send_otp_via_sms(user_key, otp_code)
        if not sent_ok:
            return False, {"message": "Failed to send SMS. Please check provider configuration."}
        return True, {
            "otp": otp_code,
            "expires_at": float((device_record["expires_at"] if "expires_at" in device_record else None)),
            "resend_available_in_seconds": 0,
            "sent": True,
        }

    otp_code = generate_otp()
    expires_at = now + OTP_VALID_SECONDS
    user_record["send_timestamps"].append(now)
    user_record.setdefault("devices", {})[device_key] = {
        "otp": otp_code,
        "created_at": now,
        "expires_at": expires_at,
        "last_sent_at": now,
        "verify_attempts": 0,
    }
    sent_ok = send_otp_via_sms(user_key, otp_code)
    if not sent_ok:
        return False, {"message": "Failed to send SMS. Please check provider configuration."}
    return True, {"otp": otp_code, "expires_at": expires_at, "resend_available_in_seconds": 0, "sent": True}


def _mem_verify_otp(
    user_key: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    now = time.time()
    user_record = _get_user_record(user_key)
    if not user_record:
        return {"valid": False, "message": "OTP not found or expired"}
    stored = _get_device_record(user_record, device_key, now=now)
    if not stored:
        return {"valid": False, "message": "OTP not found or expired"}

    verify_attempts = int((stored["verify_attempts"] if "verify_attempts" in stored else None) or 0)
    stored["verify_attempts"] = verify_attempts + 1

    if verify_attempts + 1 >= 5:
        (user_record["devices"] if "devices" in user_record else {}).pop(device_key, None)
        return {"valid": False, "message": "Too many attempts. Please request a new OTP"}

    if str((stored["otp"] if "otp" in stored else None)) == str(provided_otp):
        if delete_on_success:
            (user_record["devices"] if "devices" in user_record else {}).pop(device_key, None)
        return {"valid": True, "message": "OTP verified"}

    provider = os.getenv("SMS_PROVIDER", "msg91")
    is_dev = os.getenv("ENVIRONMENT") == "development" and not os.getenv("FORCE_SMS")
    if provider == "msg91" and not is_dev:
        ok, res_data = verify_otp_via_msg91_headless(user_key, provided_otp)
        if ok:
            if delete_on_success:
                (user_record["devices"] if "devices" in user_record else {}).pop(device_key, None)
            return {"valid": True, "message": "OTP verified"}
        else:
            return {"valid": False, "message": (res_data["message"] if "message" in res_data else None) or "Invalid OTP"}

    return {"valid": False, "message": "Invalid OTP"}


# ─── Public API (MySQL Relational DB mode) ───


def request_otp(user_key: str, device_key: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Request (send/resend) an OTP.
    Since we are using MySQL DB, callers must await the result (use request_otp_async).
    """
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        raise RuntimeError("Use request_otp_async in async context")
    return loop.run_until_complete(_db_request_otp(user_key, device_key))


async def request_otp_async(user_key: str, device_key: str) -> Tuple[bool, Dict[str, Any]]:
    """Async version of request_otp. Use this from async route handlers."""
    return await _db_request_otp(user_key, device_key)


def verify_otp(
    user_key: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    """Verify OTP. Use verify_otp_async from async context."""
    raise RuntimeError("Use verify_otp_async in async context")


async def verify_otp_async(
    user_key: str, provided_otp: str, device_key: str = "default", delete_on_success: bool = True
) -> Dict[str, Any]:
    """Async version of verify_otp. Use this from async route handlers."""
    return await _db_verify_otp(user_key, provided_otp, device_key, delete_on_success)


def get_otp(user_key: str, device_key: str = "default") -> Optional[str]:
    """Get OTP for user+device (for development/testing, in-memory only)"""
    user_record = otp_store[user_key] if user_key in otp_store else None
    if not user_record or not isinstance((user_record["devices"] if "devices" in user_record else None), dict):
        return None
    device = (user_record["devices"][device_key] if device_key in user_record["devices"] else None)
    if not device:
        return None
    return str((device["otp"] if "otp" in device else None))
