"""
Oracle DAO for sj_sessions. Implements FileStorage-like interface for 'sessions'.
"""

from app.config.settings import settings
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


def _to_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class OracleSessionDAO:

    @property
    def TABLE(self):
        suffix = getattr(settings, 'table_suffix', '')
        return f"sj_sessions{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "user": str(r.user_id),
            "userId": str(r.user_id),
            "refreshTokenId": r.refresh_token_id,
            "status": r.status,
            "lastActiveAt": r.last_active_at.isoformat() if r.last_active_at else None,
            "revokedAt": r.revoked_at.isoformat() if r.revoked_at else None,
            "revokedReason": r.revoked_reason,
            "device": json_loads(r.device) or {},
            "isGuest": bool(r.is_guest) if r.is_guest is not None else False,
            "comment": r.comments,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, device, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
        docs = [self._row_to_doc(r) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.get("_id")) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        sid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, device, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": sid},
            )
            row = result.fetchone()
        return self._row_to_doc(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id_raw = data.get("userId") or data.get("user")
        user_id = int(user_id_raw) if str(user_id_raw or "").isdigit() else None
        if user_id is None:
            raise ValueError("Session user must be numeric id when using Oracle")

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, refresh_token_id, status, last_active_at,
                        revoked_at, revoked_reason, device, is_guest, comments, created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id, :refresh_token_id, :status, :last_active_at,
                        :revoked_at, :revoked_reason, :device, :is_guest, :comments, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "refresh_token_id": data.get("refreshTokenId"),
                    "status": data.get("status"),
                    "last_active_at": _to_ts(data.get("lastActiveAt")),
                    "revoked_at": _to_ts(data.get("revokedAt")),
                    "revoked_reason": data.get("revokedReason"),
                    "device": json_dumps(data.get("device") or {}),
                    "is_guest": 1 if data.get("isGuest") else 0,
                    "comments": data.get("comment"),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        sid = int(id) if str(id).isdigit() else 0
        user_id_raw = merged.get("userId") or merged.get("user")
        user_id = int(user_id_raw) if str(user_id_raw or "").isdigit() else None
        if user_id is None:
            return None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        user_id = :user_id,
                        refresh_token_id = :refresh_token_id,
                        status = :status,
                        last_active_at = :last_active_at,
                        revoked_at = :revoked_at,
                        revoked_reason = :revoked_reason,
                        device = :device,
                        is_guest = :is_guest,
                        comments = :comments,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": sid,
                    "user_id": user_id,
                    "refresh_token_id": merged.get("refreshTokenId"),
                    "status": merged.get("status"),
                    "last_active_at": _to_ts(merged.get("lastActiveAt")),
                    "revoked_at": _to_ts(merged.get("revokedAt")),
                    "revoked_reason": merged.get("revokedReason"),
                    "device": json_dumps(merged.get("device") or {}),
                    "is_guest": 1 if merged.get("isGuest") else 0,
                    "comments": merged.get("comment"),
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def touch(self, session_id: str, device: dict = None) -> None:
        """Lightweight session touch — single UPDATE, no reads. Fire-and-forget."""
        factory = self._factory()
        if not factory:
            return
        sid = int(session_id) if str(session_id).isdigit() else 0
        if not sid:
            return
        now = now_utc()
        try:
            async with factory() as session:
                if device:
                    await session.execute(
                        text(
                            f"""
                            UPDATE {self.TABLE}
                            SET last_active_at = :now, device = :device, updated_at = :now
                            WHERE id = :id AND status = 'active'
                            """
                        ),
                        {"now": now, "device": json_dumps(device), "id": sid},
                    )
                else:
                    await session.execute(
                        text(
                            f"""
                            UPDATE {self.TABLE}
                            SET last_active_at = :now, updated_at = :now
                            WHERE id = :id AND status = 'active'
                            """
                        ),
                        {"now": now, "id": sid},
                    )
                await session.commit()
        except Exception:
            pass  # Fire-and-forget — don't break the request on touch failure

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        sid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": sid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def delete_by_user_id(self, user_id: str) -> int:
        """Delete all sessions for a user with a single targeted SQL DELETE.
        Used in test teardown to avoid FK_SJ_SESSIONS_USER constraint violations."""
        factory = self._factory()
        if not factory:
            return 0
        uid = int(user_id) if str(user_id).isdigit() else None
        if uid is None:
            return 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": uid},
            )
            await session.commit()
            return result.rowcount

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    touch_session = touch
