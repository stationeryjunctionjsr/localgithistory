from datetime import datetime
from typing import List, Optional
from app.models.schemas import SellerPayoutDetailResponse
from app.models.daos import SellerPayoutInternalCreate, SellerPayoutInternalUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLSellerPayoutDAO:
    TABLE = "sj_seller_payouts"

    def _map_row(self, row) -> SellerPayoutDetailResponse:
        return SellerPayoutDetailResponse.model_validate(row)

    async def _fetch_sub_orders(self, payout_id: int) -> List[int]:
        if not payout_id:
            return []
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(
                text("SELECT CAST(sub_order_id AS SIGNED) AS sub_order_id FROM sj_seller_payout_sub_orders WHERE payout_id = :id"),
                {"id": payout_id}
            )).fetchall()
        return [r.sub_order_id for r in rows if r.sub_order_id is not None]

    async def _save_sub_orders(self, session, payout_id: int, sub_order_ids: List[int]):
        await session.execute(
            text("DELETE FROM sj_seller_payout_sub_orders WHERE payout_id = :id"),
            {"id": payout_id}
        )
        if sub_order_ids:
            for soid in sub_order_ids:
                await session.execute(
                    text("INSERT INTO sj_seller_payout_sub_orders (payout_id, sub_order_id) VALUES (:pid, :soid)"),
                    {"pid": payout_id, "soid": soid}
                )

    async def findAll(self, seller_id: Optional[str] = None) -> List[SellerPayoutDetailResponse]:
        where_clauses = []
        params = {}
        if seller_id is not None:
            where_clauses.append("seller_id = :seller_id")
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id DESC"),
                    params,
                )
            ).fetchall()
        
        records = [self._map_row(r) for r in rows]
        for r in records:
            r.sub_order_ids = await self._fetch_sub_orders(r.id)
        return records

    async def findOne(
        self,
        id: Optional[int] = None,
        seller_id: Optional[str] = None,
    ) -> Optional[SellerPayoutDetailResponse]:
        if id is not None:
            return await self.findById(id)
        records = await self.findAll(seller_id=seller_id)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[SellerPayoutDetailResponse]:
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
        record = self._map_row(row)
        record.sub_order_ids = await self._fetch_sub_orders(record.id)
        return record

    async def create(self, data: SellerPayoutInternalCreate) -> SellerPayoutDetailResponse:
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}

        if data.seller_id is not None:
            cols.append("seller_id")
            vals.append(":seller_id")
            params["seller_id"] = data.seller_id
        if data.amount is not None:
            cols.append("amount")
            vals.append(":amount")
            params["amount"] = data.amount
        if data.period_start is not None:
            cols.append("period_start")
            vals.append(":period_start")
            params["period_start"] = _parse_dt(data.period_start)
        if data.period_end is not None:
            cols.append("period_end")
            vals.append(":period_end")
            params["period_end"] = _parse_dt(data.period_end)
        if data.notes is not None:
            cols.append("notes")
            vals.append(":notes")
            params["notes"] = data.notes
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status

        sub_orders = (data.sub_order_ids if data.sub_order_ids is not None else [])

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = result.lastrowid
            await self._save_sub_orders(session, new_id, sub_orders)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: SellerPayoutInternalUpdate) -> Optional[SellerPayoutDetailResponse]:
        if not id:
            return None
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "seller_id" in update_data.model_fields_set:
            updates.append("seller_id = :seller_id")
            params["seller_id"] = update_data.seller_id
        if "amount" in update_data.model_fields_set:
            updates.append("amount = :amount")
            params["amount"] = update_data.amount
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
        if "seller_received_at" in update_data.model_fields_set:
            updates.append("seller_received_at = :seller_received_at")
            params["seller_received_at"] = _parse_dt(update_data.seller_received_at)
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
            if "sub_order_ids" in update_data.model_fields_set:
                await self._save_sub_orders(session, id, update_data.sub_order_ids or [])
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
