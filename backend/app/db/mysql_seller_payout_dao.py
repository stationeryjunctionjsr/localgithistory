import secrets
from typing import Dict, Any, List, Optional
from app.models.schemas import SellerPayoutDetailResponse
from app.models.seller_payout import SellerPayout, List, Optional
from app.models.daos import SellerPayoutInternalCreate, SellerPayoutInternalUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLSellerPayoutDAO:
    TABLE = "sj_seller_payouts"

    def _factory(self):
        return get_async_session_factory()

    def _map_row(self, row) -> SellerPayoutDetailResponse:
        return SellerPayoutDetailResponse(
            id=str(row.id),
            sellerId=row.seller_id,
            amount=float(row.amount) if row.amount is not None else 0.0,
            periodStart=row.period_start.isoformat() + "Z" if row.period_start else None,
            periodEnd=row.period_end.isoformat() + "Z" if row.period_end else None,
            status=row.status if row.status else 'pending_payment',
            paymentMethod=row.payment_method,
            paymentReference=row.payment_reference,
            adminPaidAt=row.admin_paid_at.isoformat() + "Z" if row.admin_paid_at else None,
            adminPaidBy=row.admin_paid_by,
            sellerReceivedAt=row.seller_received_at.isoformat() + "Z" if row.seller_received_at else None,
            notes=row.notes,
            createdAt=row.created_at.isoformat() + "Z" if row.created_at else None,
            updatedAt=row.updated_at.isoformat() + "Z" if row.updated_at else None,
        )

    async def _fetch_sub_orders(self, payout_id: str) -> List[str]:
        factory = self._factory()
        pid = int(payout_id) if str(payout_id).isdigit() else None
        async with factory() as session:
            rows = (await session.execute(
                text("SELECT sub_order_id FROM sj_seller_payout_sub_orders WHERE payout_id = :id"),
                {"id": pid}
            )).fetchall()
        return [r.sub_order_id for r in rows]

    async def _save_sub_orders(self, session, payout_id: int, sub_order_ids: List[str]):
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

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "sellerId" in query:
            where_clauses.append("seller_id = :sellerId")
            params["sellerId"] = query["sellerId"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id DESC"),
                    params,
                )
            ).fetchall()
        
        docs = [self._map_row(r) for r in rows]
        for d in docs:
            d.subOrderIds = await self._fetch_sub_orders(d.id)
        return docs

    async def findOne(self, query: Dict) -> Optional[SellerPayoutDetailResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
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
        doc = self._map_row(row)
        doc.subOrderIds = await self._fetch_sub_orders(doc.id)
        return doc

    async def create(self, data: SellerPayoutInternalCreate) -> SellerPayoutDetailResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}

        if data.seller_id is not None:
            cols.append("seller_id")
            vals.append(":sellerId")
            params["sellerId"] = data.seller_id
        if data.amount is not None:
            cols.append("amount")
            vals.append(":amount")
            params["amount"] = data.amount
        if data.periodStart is not None:
            cols.append("period_start")
            vals.append(":periodStart")
            params["periodStart"] = _parse_dt(data.periodStart)
        if data.periodEnd is not None:
            cols.append("period_end")
            vals.append(":periodEnd")
            params["periodEnd"] = _parse_dt(data.periodEnd)
        if data.notes is not None:
            cols.append("notes")
            vals.append(":notes")
            params["notes"] = data.notes
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status

        sub_orders = (data.subOrderIds if data.subOrderIds is not None else [])

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await self._save_sub_orders(session, new_id, sub_orders)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: SellerPayoutInternalUpdate) -> Optional[Dict]:
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

        _handle_field("sellerId", "seller_id", data.seller_id, existing.seller_id)
        _handle_field("amount", "amount", data.amount, existing.amount)
        _handle_field("periodStart", "period_start", data.periodStart, existing.periodStart, True)
        _handle_field("periodEnd", "period_end", data.periodEnd, existing.periodEnd, True)
        _handle_field("status", "status", data.status, existing.status)
        _handle_field("paymentMethod", "payment_method", data.payment_method, existing.payment_method)
        _handle_field("paymentReference", "payment_reference", data.paymentReference, existing.paymentReference)
        _handle_field("adminPaidAt", "admin_paid_at", data.adminPaidAt, existing.adminPaidAt, True)
        _handle_field("adminPaidBy", "admin_paid_by", data.adminPaidBy, existing.adminPaidBy)
        _handle_field("sellerReceivedAt", "seller_received_at", data.sellerReceivedAt, existing.sellerReceivedAt, True)
        _handle_field("notes", "notes", data.notes, existing.notes)

        sub_orders = data.subOrderIds if data.subOrderIds is not None else existing.subOrderIds

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if sub_orders is not None:
                await self._save_sub_orders(session, pid, sub_orders)
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


