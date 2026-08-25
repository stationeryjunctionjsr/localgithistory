"""
Oracle DAO for OTP storage (sj_otps + sj_otp_send_log).
Replaces the in-memory dict-based OTP store with DB-backed persistence and TTL.
"""

from app.config.settings import settings
from datetime import timedelta
from typing import Dict, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import now_utc


class OracleOtpDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_otps{suffix}"

    @property
    def SEND_LOG_TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_otp_send_log{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def find_active_otp(self, phone: str, device_key: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        async with factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, phone, device_key, otp_code, verify_attempts,
                           created_at, expires_at, last_sent_at
                    FROM {self.TABLE}
                    WHERE phone = :phone AND device_key = :device_key
                      AND expires_at > :now
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"phone": phone, "device_key": device_key, "now": now},
            )
            row = result.fetchone()
        if not row:
            return None
        return {
            "id": row.id,
            "phone": row.phone,
            "device_key": row.device_key,
            "otp": row.otp_code,
            "verify_attempts": row.verify_attempts or 0,
            "created_at": row.created_at.timestamp() if row.created_at else 0,
            "expires_at": row.expires_at.timestamp() if row.expires_at else 0,
            "last_sent_at": row.last_sent_at.timestamp() if row.last_sent_at else 0,
        }

    async def create_otp(
        self,
        phone: str,
        device_key: str,
        otp_code: str,
        valid_seconds: int,
    ) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        expires = now + timedelta(seconds=valid_seconds)
        async with factory() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE}
                        (phone, device_key, otp_code, verify_attempts, created_at, expires_at, last_sent_at)
                    VALUES
                        (:phone, :device_key, :otp_code, 0, :created_at, :expires_at, :last_sent_at)
                """),
                {
                    "phone": phone,
                    "device_key": device_key,
                    "otp_code": otp_code,
                    "created_at": now,
                    "expires_at": expires,
                    "last_sent_at": now,
                },
            )
            await session.commit()
        return {
            "otp": otp_code,
            "created_at": now.timestamp(),
            "expires_at": expires.timestamp(),
            "last_sent_at": now.timestamp(),
            "verify_attempts": 0,
        }

    async def update_last_sent(self, otp_id: int) -> None:
        factory = self._factory()
        if not factory:
            return
        now = now_utc()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET last_sent_at = :now WHERE id = :id"),
                {"now": now, "id": otp_id},
            )
            await session.commit()

    async def increment_attempts(self, otp_id: int) -> None:
        factory = self._factory()
        if not factory:
            return
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET verify_attempts = verify_attempts + 1 WHERE id = :id"),
                {"id": otp_id},
            )
            await session.commit()

    async def delete_otp(self, otp_id: int) -> None:
        factory = self._factory()
        if not factory:
            return
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": otp_id},
            )
            await session.commit()

    async def cleanup_expired(self) -> int:
        """Remove all expired OTPs. Call periodically or on startup."""
        factory = self._factory()
        if not factory:
            return 0
        now = now_utc()
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE expires_at <= :now"),
                {"now": now},
            )
            await session.commit()
            return result.rowcount

    # --- Send log (user-level hourly rate limit) ---

    async def record_send(self, phone: str) -> None:
        factory = self._factory()
        if not factory:
            return
        now = now_utc()
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.SEND_LOG_TABLE} (phone, sent_at) VALUES (:phone, :sent_at)"),
                {"phone": phone, "sent_at": now},
            )
            await session.commit()

    async def count_sends_in_window(self, phone: str, window_seconds: int) -> int:
        factory = self._factory()
        if not factory:
            return 0
        threshold = now_utc() - timedelta(seconds=window_seconds)
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {self.SEND_LOG_TABLE} WHERE phone = :phone AND sent_at >= :threshold"),
                {"phone": phone, "threshold": threshold},
            )
            return result.scalar() or 0

    async def cleanup_old_send_logs(self, window_seconds: int) -> int:
        factory = self._factory()
        if not factory:
            return 0
        threshold = now_utc() - timedelta(seconds=window_seconds)
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.SEND_LOG_TABLE} WHERE sent_at < :threshold"),
                {"threshold": threshold},
            )
            await session.commit()
            return result.rowcount


otp_dao = OracleOtpDAO()
