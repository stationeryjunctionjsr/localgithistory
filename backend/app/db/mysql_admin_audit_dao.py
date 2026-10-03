"""
MySQL DAO for sj_admin_audit_log.

Write-only insert path — audit rows are never updated or deleted.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

logger = logging.getLogger(__name__)


class MySQLAdminAuditDAO:
    TABLE = "sj_admin_audit_log"

    def _factory(self):
        return get_async_session_factory()

    async def log(
        self,
        *,
        actor_id: str,
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str],
        change_summary: Optional[dict],
        ip_address: Optional[str] = None,
    ) -> None:
        """Insert one audit row. Fire-and-forget — failures are logged, never raised."""
        factory = self._factory()
        if not factory:
            return
        now: datetime = now_utc()
        summary_json: Optional[str] = json.dumps(change_summary, default=str) if change_summary else None
        try:
            async with factory() as session:
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE}
                            (actor_id, actor_role, action, entity_type, entity_id,
                             change_summary, ip_address, created_at)
                        VALUES
                            (:actor_id, :actor_role, :action, :entity_type, :entity_id,
                             :change_summary, :ip_address, :created_at)
                        """
                    ),
                    {
                        "actor_id": str(actor_id),
                        "actor_role": actor_role,
                        "action": action,
                        "entity_type": entity_type,
                        "entity_id": str(entity_id) if entity_id is not None else None,
                        "change_summary": summary_json,
                        "ip_address": ip_address,
                        "created_at": now,
                    },
                )
                await session.commit()
        except Exception as exc:
            # Audit logging must never take down a request
            logger.error(
                "admin_audit_dao.log: failed to write audit row "
                "(actor=%s action=%s entity=%s/%s): %s",
                actor_id,
                action,
                entity_type,
                entity_id,
                exc,
                exc_info=True,
            )


admin_audit_dao = MySQLAdminAuditDAO()
