from datetime import datetime
from typing import List, Optional
from app.models.schemas import SellerPayoutDetailResponse
from app.models.daos import SellerPayoutInternalCreate, SellerPayoutInternalUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLSellerPayoutDAO:
    TABLE = "sj_seller_payouts"

    def _factory(self):
        return get_async_session_factory()

    def _map_row(self, row) -> SellerPayoutDetailResponse:
        return SellerPayoutDetailResponse.model_validate(row)

    async def _fetch_sub_orders(self, payout_id: int) -> List[int]:
        factory = self._factory()
        if not factory or not payout_id:
            return []
        async with factory() as session:
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
        factory = self._factory()
        async with factory() as session:
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
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
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
        factory = self._factory()
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
        async with factory() as session:
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
        existing = await self.findById(id)
        if not existing:
            return None
        
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        def _handle_field(api_k, db_k, new_val, existing_val, is_date=False):
            if new_val is not None:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = _parse_dt(new_val) if is_date else new_val
            else:
                if existing_val is not None:
                    updates.append(f"{db_k} = :{api_k}")
                    params[api_k] = _parse_dt(existing_val) if is_date else existing_val

        _handle_field("seller_id", "seller_id", update_data.seller_id, existing.seller_id)
        _handle_field("amount", "amount", update_data.amount, existing.amount)
        _handle_field("period_start", "period_start", update_data.period_start, existing.period_start, True)
        _handle_field("period_end", "period_end", update_data.period_end, existing.period_end, True)
        _handle_field("status", "status", update_data.status, existing.status)
        _handle_field("payment_method", "payment_method", update_data.payment_method, existing.payment_method)
        _handle_field("payment_reference", "payment_reference", update_data.payment_reference, existing.payment_reference)
        _handle_field("admin_paid_at", "admin_paid_at", update_data.admin_paid_at, existing.admin_paid_at, True)
        _handle_field("admin_paid_by", "admin_paid_by", update_data.admin_paid_by, existing.admin_paid_by)
        _handle_field("seller_received_at", "seller_received_at", update_data.seller_received_at, existing.seller_received_at, True)
        _handle_field("notes", "notes", update_data.notes, existing.notes)

        sub_orders = update_data.sub_order_ids if update_data.sub_order_ids is not None else existing.sub_order_ids

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if sub_orders is not None:
                await self._save_sub_orders(session, id, sub_orders)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
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
