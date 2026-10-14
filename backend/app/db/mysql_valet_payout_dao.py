from datetime import datetime
from typing import List, Optional
from app.models.schemas import ValetPayoutDetailResponse
from app.models.daos import ValetPayoutInternalCreate, ValetPayoutInternalUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLValetPayoutDAO:
    TABLE = "sj_valet_payouts"

    def _map_row(self, row) -> ValetPayoutDetailResponse:
        return ValetPayoutDetailResponse.model_validate(row)

    async def findAll(
        self,
        valet_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ValetPayoutDetailResponse]:
        where_clauses = []
        params = {}
        if valet_id is not None:
            where_clauses.append("valet_id = :valet_id")
            params["valet_id"] = valet_id
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id DESC"),
                    params,
                )
            ).fetchall()
        
        return [self._map_row(r) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        valet_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[ValetPayoutDetailResponse]:
        if id is not None:
            return await self.findById(id)
        records = await self.findAll(valet_id=valet_id, status=status)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ValetPayoutDetailResponse]:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        
        if not row:
            return None
        return self._map_row(row)

    async def create(self, data: ValetPayoutInternalCreate) -> ValetPayoutDetailResponse:
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}

        if data.valet_id is not None:
            cols.append("valet_id")
            vals.append(":valet_id")
            params["valet_id"] = data.valet_id
        if data.amount is not None:
            cols.append("amount")
            vals.append(":amount")
            params["amount"] = data.amount
        if data.delivery_count is not None:
            cols.append("delivery_count")
            vals.append(":delivery_count")
            params["delivery_count"] = data.delivery_count
        if data.return_count is not None:
            cols.append("return_count")
            vals.append(":return_count")
            params["return_count"] = data.return_count
        if data.period_start is not None:
            cols.append("period_start")
            vals.append(":period_start")
            params["period_start"] = _parse_dt(data.period_start)
        if data.period_end is not None:
            cols.append("period_end")
            vals.append(":period_end")
            params["period_end"] = _parse_dt(data.period_end)
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if data.payment_method is not None:
            cols.append("payment_method")
            vals.append(":payment_method")
            params["payment_method"] = data.payment_method
        if data.payment_reference is not None:
            cols.append("payment_reference")
            vals.append(":payment_reference")
            params["payment_reference"] = data.payment_reference
        if data.admin_paid_at is not None:
            cols.append("admin_paid_at")
            vals.append(":admin_paid_at")
            params["admin_paid_at"] = _parse_dt(data.admin_paid_at)
        if data.admin_paid_by is not None:
            cols.append("admin_paid_by")
            vals.append(":admin_paid_by")
            params["admin_paid_by"] = data.admin_paid_by
        if data.valet_received_at is not None:
            cols.append("valet_received_at")
            vals.append(":valet_received_at")
            params["valet_received_at"] = _parse_dt(data.valet_received_at)
        if data.notes is not None:
            cols.append("notes")
            vals.append(":notes")
            params["notes"] = data.notes

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = result.lastrowid
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: ValetPayoutInternalUpdate) -> Optional[ValetPayoutDetailResponse]:
        if not id:
            return None
        
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "valet_id" in update_data.model_fields_set:
            updates.append("valet_id = :valet_id")
            params["valet_id"] = update_data.valet_id
        if "amount" in update_data.model_fields_set:
            updates.append("amount = :amount")
            params["amount"] = update_data.amount
        if "delivery_count" in update_data.model_fields_set:
            updates.append("delivery_count = :delivery_count")
            params["delivery_count"] = update_data.delivery_count
        if "return_count" in update_data.model_fields_set:
            updates.append("return_count = :return_count")
            params["return_count"] = update_data.return_count
        if "period_start" in update_data.model_fields_set:
            updates.append("period_start = :period_start")
            params["period_start"] = _parse_dt(update_data.period_start)
        if "period_end" in update_data.model_fields_set:
            updates.append("period_end = :period_end")
            params["period_end"] = _parse_dt(update_data.period_end)
        if "status" in update_data.model_fields_set:
            updates.append("status = :status")
            params["status"] = update_data.status
        if "payment_method" in update_data.model_fields_set:
            updates.append("payment_method = :payment_method")
            params["payment_method"] = update_data.payment_method
        if "payment_reference" in update_data.model_fields_set:
            updates.append("payment_reference = :payment_reference")
            params["payment_reference"] = update_data.payment_reference
        if "admin_paid_at" in update_data.model_fields_set:
            updates.append("admin_paid_at = :admin_paid_at")
            params["admin_paid_at"] = _parse_dt(update_data.admin_paid_at)
        if "admin_paid_by" in update_data.model_fields_set:
            updates.append("admin_paid_by = :admin_paid_by")
            params["admin_paid_by"] = update_data.admin_paid_by
        if "valet_received_at" in update_data.model_fields_set:
            updates.append("valet_received_at = :valet_received_at")
            params["valet_received_at"] = _parse_dt(update_data.valet_received_at)
        if "notes" in update_data.model_fields_set:
            updates.append("notes = :notes")
            params["notes"] = update_data.notes

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
            if res.rowcount == 0:
                existing = await self.findById(id)
                if not existing:
                    return None
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0


def _parse_dt(dt_val: Optional[str]):
    if dt_val:
        if dt_val.endswith("Z"):
            dt_val = dt_val[:-1] + "+00:00"
        dt_val = dt_val.replace("+00:00+00:00", "+00:00")
        try:
            dt = datetime.fromisoformat(dt_val)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            pass
    return dt_val
