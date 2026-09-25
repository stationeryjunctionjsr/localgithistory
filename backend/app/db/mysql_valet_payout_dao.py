import secrets
from typing import Dict, Any, List, Optional
from app.models.schemas import ValetPayoutDetailResponse
from app.models.daos import ValetPayoutInternalCreate, ValetPayoutInternalUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLValetPayoutDAO:
    TABLE = "sj_valet_payouts"

    def _factory(self):
        return get_async_session_factory()

    def _map_row(self, row) -> ValetPayoutDetailResponse:
        return ValetPayoutDetailResponse(
            id=str(row.id),
            valetId=row.valet_id,
            amount=float(row.amount) if row.amount is not None else 0.0,
            deliveryCount=row.delivery_count if row.delivery_count is not None else 0,
            returnCount=row.return_count if row.return_count is not None else 0,
            periodStart=row.period_start.isoformat() + "Z" if row.period_start else None,
            periodEnd=row.period_end.isoformat() + "Z" if row.period_end else None,
            status=row.status if row.status else 'pending_payment',
            paymentMethod=row.payment_method,
            paymentReference=row.payment_reference,
            adminPaidAt=row.admin_paid_at.isoformat() + "Z" if row.admin_paid_at else None,
            adminPaidBy=row.admin_paid_by,
            valetReceivedAt=row.valet_received_at.isoformat() + "Z" if row.valet_received_at else None,
            notes=row.notes,
            createdAt=row.created_at.isoformat() + "Z" if row.created_at else None,
            updatedAt=row.updated_at.isoformat() + "Z" if row.updated_at else None,
        )

    async def findAll(self, query: Dict = None) -> List[ValetPayoutDetailResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "valetId" in query:
            where_clauses.append("valet_id = :valetId")
            params["valetId"] = query["valetId"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id DESC"),
                    params,
                )
            ).fetchall()
        
        return [self._map_row(r) for r in rows]

    async def findOne(self, query: Dict) -> Dict:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[ValetPayoutDetailResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        
        if not row:
            return None
        return self._map_row(row)

    async def create(self, data: ValetPayoutInternalCreate) -> ValetPayoutDetailResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}

        if data.valet_id is not None:
            cols.append("valet_id")
            vals.append(":valetId")
            params["valetId"] = data.valet_id
        if data.amount is not None:
            cols.append("amount")
            vals.append(":amount")
            params["amount"] = data.amount
        if data.delivery_count is not None:
            cols.append("delivery_count")
            vals.append(":deliveryCount")
            params["deliveryCount"] = data.delivery_count
        if data.return_count is not None:
            cols.append("return_count")
            vals.append(":returnCount")
            params["returnCount"] = data.return_count
        if data.period_start is not None:
            cols.append("period_start")
            vals.append(":periodStart")
            params["periodStart"] = _parse_dt(data.period_start)
        if data.period_end is not None:
            cols.append("period_end")
            vals.append(":periodEnd")
            params["periodEnd"] = _parse_dt(data.period_end)
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if data.payment_method is not None:
            cols.append("payment_method")
            vals.append(":paymentMethod")
            params["paymentMethod"] = data.payment_method
        if data.payment_reference is not None:
            cols.append("payment_reference")
            vals.append(":paymentReference")
            params["paymentReference"] = data.payment_reference
        if data.admin_paid_at is not None:
            cols.append("admin_paid_at")
            vals.append(":adminPaidAt")
            params["adminPaidAt"] = _parse_dt(data.admin_paid_at)
        if data.admin_paid_by is not None:
            cols.append("admin_paid_by")
            vals.append(":adminPaidBy")
            params["adminPaidBy"] = data.admin_paid_by
        if data.valet_received_at is not None:
            cols.append("valet_received_at")
            vals.append(":valetReceivedAt")
            params["valetReceivedAt"] = _parse_dt(data.valet_received_at)
        if data.notes is not None:
            cols.append("notes")
            vals.append(":notes")
            params["notes"] = data.notes

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ValetPayoutInternalUpdate) -> Optional[ValetPayoutDetailResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}

        def _handle_field(api_k, db_k, new_val, existing_val, is_date=False):
            if new_val is not None:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = _parse_dt(new_val) if is_date else new_val
            else:
                if existing_val is not None:
                    updates.append(f"{db_k} = :{api_k}")
                    params[api_k] = _parse_dt(existing_val) if is_date else existing_val

        _handle_field("valetId", "valet_id", data.valet_id, existing.valet_id)
        _handle_field("amount", "amount", data.amount, existing.amount)
        _handle_field("deliveryCount", "delivery_count", data.delivery_count, existing.delivery_count)
        _handle_field("returnCount", "return_count", data.return_count, existing.return_count)
        _handle_field("periodStart", "period_start", data.period_start, existing.period_start, True)
        _handle_field("periodEnd", "period_end", data.period_end, existing.period_end, True)
        _handle_field("status", "status", data.status, existing.status)
        _handle_field("paymentMethod", "payment_method", data.payment_method, existing.payment_method)
        _handle_field("paymentReference", "payment_reference", data.payment_reference, existing.payment_reference)
        _handle_field("adminPaidAt", "admin_paid_at", data.admin_paid_at, existing.admin_paid_at, True)
        _handle_field("adminPaidBy", "admin_paid_by", data.admin_paid_by, existing.admin_paid_by)
        _handle_field("valetReceivedAt", "valet_received_at", data.valet_received_at, existing.valet_received_at, True)
        _handle_field("notes", "notes", data.notes, existing.notes)

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0
def _parse_dt(dt_val):
    if isinstance(dt_val, str):
        if dt_val.endswith("Z"):
            dt_val = dt_val[:-1] + "+00:00"
        dt_val = dt_val.replace("+00:00+00:00", "+00:00")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_val)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            pass
    return dt_val


