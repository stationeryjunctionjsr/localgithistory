"""
order_timeline.py
=================
Utilities for logging and fetching order status history.

Table: sj_order_status_history
  id           INT AUTO_INCREMENT PK
  order_id     INT  FK → sj_orders.id ON DELETE CASCADE
  status       VARCHAR(32)
  changed_by   VARCHAR(64)   — user_id or 'system'
  changed_at   DATETIME
  note         VARCHAR(1024)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.utils.logger import logger

# ---------------------------------------------------------------------------
# DDL — runs once on first use (IF NOT EXISTS guard)
# ---------------------------------------------------------------------------
_TABLE_ENSURED = False

_CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS sj_order_status_history (
      id          INT NOT NULL AUTO_INCREMENT,
      order_id    INT NOT NULL,
      status      VARCHAR(32) NOT NULL,
      changed_by  VARCHAR(64) DEFAULT NULL,
      changed_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
      note        VARCHAR(1024) DEFAULT NULL,
      PRIMARY KEY (id),
      KEY ix_osh_order     (order_id),
      KEY ix_osh_changed_at (changed_at),
      CONSTRAINT fk_osh_order FOREIGN KEY (order_id)
        REFERENCES sj_orders (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")


async def _ensure_table():
    global _TABLE_ENSURED
    if _TABLE_ENSURED:
        return
    factory = get_async_session_factory()
    if not factory:
        return
    try:
        async with factory() as session:
            await session.execute(_CREATE_TABLE_SQL)
            await session.commit()
        _TABLE_ENSURED = True
    except Exception as e:
        logger.warning("order_timeline: could not ensure table: %s", e)


# ---------------------------------------------------------------------------
# log_order_status — call after every status transition
# ---------------------------------------------------------------------------
async def log_order_status(
    order_id: int,
    status: str,
    changed_by: Optional[str] = "system",
    note: Optional[str] = None,
) -> None:
    """Insert one row into sj_order_status_history. Fire-and-forget safe."""
    await _ensure_table()
    factory = get_async_session_factory()
    if not factory:
        return
    try:
        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO sj_order_status_history "
                    "(order_id, status, changed_by, changed_at, note) "
                    "VALUES (:order_id, :status, :changed_by, :changed_at, :note)"
                ),
                {
                    "order_id": int(order_id),
                    "status": status,
                    "changed_by": str(changed_by) if changed_by else "system",
                    "changed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "note": note,
                },
            )
            await session.commit()
    except Exception as e:
        logger.warning("order_timeline: log_order_status failed for order %s → %s: %s", order_id, status, e)


# ---------------------------------------------------------------------------
# get_order_timeline — returns list of {status, changed_at, changed_by, note}
# Falls back to synthesising history from sj_orders columns when the history
# table is empty (handles orders placed before this feature was added).
# ---------------------------------------------------------------------------
async def get_order_timeline(order_id: int) -> list[dict]:
    """Return status history for an order, newest-last."""
    await _ensure_table()
    factory = get_async_session_factory()
    if not factory:
        return []

    rows = []
    try:
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT status, changed_at, changed_by, note "
                    "FROM sj_order_status_history "
                    "WHERE order_id = :oid "
                    "ORDER BY changed_at ASC, id ASC"
                ),
                {"oid": order_id},
            )
            rows = [
                {
                    "status": r.status,
                    "changedAt": r.changed_at.isoformat() + "Z" if isinstance(r.changed_at, datetime) else str(r.changed_at),
                    "changedBy": r.changed_by,
                    "note": r.note,
                }
                for r in result.fetchall()
            ]

            # If no history yet, synthesise from sj_orders timestamps (backfill)
            if not rows:
                ord_result = await session.execute(
                    text(
                        "SELECT status, created_at, shipped_at, delivered_at, cancelled_at "
                        "FROM sj_orders WHERE id = :oid"
                    ),
                    {"oid": order_id},
                )
                ord_row = ord_result.fetchone()
                if ord_row:
                    def _ts(dt) -> str:
                        if dt is None:
                            return None
                        return dt.isoformat() + "Z" if isinstance(dt, datetime) else str(dt)

                    # Always start with 'placed'
                    if ord_row.created_at:
                        rows.append({"status": "placed", "changedAt": _ts(ord_row.created_at), "changedBy": None, "note": None})

                    current = ord_row.status or "pending"

                    # If order was shipped/out_for_delivery/delivered
                    if ord_row.shipped_at:
                        rows.append({"status": "shipped", "changedAt": _ts(ord_row.shipped_at), "changedBy": None, "note": None})

                    if ord_row.delivered_at:
                        rows.append({"status": "delivered", "changedAt": _ts(ord_row.delivered_at), "changedBy": None, "note": None})
                    elif ord_row.cancelled_at:
                        rows.append({"status": "cancelled", "changedAt": _ts(ord_row.cancelled_at), "changedBy": None, "note": None})
                    elif current not in ("placed", "delivered", "cancelled") and not ord_row.shipped_at:
                        # Intermediate status — add it with updated_at approximation
                        rows.append({"status": current, "changedAt": _ts(ord_row.created_at), "changedBy": None, "note": None})

    except Exception as e:
        logger.warning("order_timeline: get_order_timeline failed for order %s: %s", order_id, e)

    return rows
