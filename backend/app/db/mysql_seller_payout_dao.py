import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import now_utc

class MySQLSellerPayoutDAO:
    TABLE = "sj_seller_payouts"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "sellerId": row.seller_id,
            "amount": float(row.amount) if row.amount is not None else 0.0,
            "periodStart": row.period_start.isoformat() if row.period_start else None,
            "periodEnd": row.period_end.isoformat() if row.period_end else None,
            "notes": row.notes,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def _fetch_sub_orders(self, payout_id: str) -> List[str]:
        factory = self._factory()
        pid = int(payout_id) if str(payout_id).isdigit() else 0
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
        
        docs = [self._row_to_dict(r) for r in rows]
        for d in docs:
            d["subOrderIds"] = await self._fetch_sub_orders(d["id"])
        return docs

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        
        if not row:
            return None
        doc = self._row_to_dict(row)
        doc["subOrderIds"] = await self._fetch_sub_orders(doc["id"])
        return doc

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}

        scalar_map = {
            "sellerId": "seller_id", "amount": "amount", "periodStart": "period_start", 
            "periodEnd": "period_end", "notes": "notes"
        }
        for api_k, db_k in scalar_map.items():
            if api_k in data:
                cols.append(db_k)
                vals.append(f":{api_k}")
                params[api_k] = data[api_k]

        sub_orders = data.get("subOrderIds", [])

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

    async def update(self, id: str, data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else 0
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}

        scalar_map = {
            "sellerId": "seller_id", "amount": "amount", "periodStart": "period_start", 
            "periodEnd": "period_end", "notes": "notes"
        }
        for api_k, db_k in scalar_map.items():
            if api_k in merged:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = merged[api_k]

        sub_orders = data.get("subOrderIds")

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
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0
