from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import ReturnRequestInternal
from app.models.daos_flat import ReturnRequestInternalCreate, ReturnRequestInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLReturnRequestsDAO:
    def __init__(self):
        self.table_name = "sj_return_requests"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional['ReturnRequestInternal']:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
            if str(id).isdigit():
                q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
                params = {"id": int(id)}
            else:
                q = text(f"SELECT * FROM {self.TABLE} WHERE external_id = :id OR return_id = :id LIMIT 1")
                params = {"id": str(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findOne(
        self,
        query: Optional[dict] = None,
        return_id: Optional[str] = None,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional['ReturnRequestInternal']:
        if return_id:
            return await self.findById(return_id)
        if query:
            rid = query.get("returnId") or query.get("return_id")
            if rid:
                return await self.findById(rid)
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, order_id=order_id, user_id=user_id)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        valet_id: Optional[str] = None,
        seller_id: Optional[str] = None,
    ) -> List['ReturnRequestInternal']:
        if query:
            if status is None and "status" in query:
                status = query["status"]
            if user_id is None:
                user_id = query.get("userId") or query.get("user_id")
            if order_id is None:
                order_id = query.get("orderId") or query.get("order_id")
            if valet_id is None:
                valet_id = query.get("valetId") or query.get("valet_id")
            if seller_id is None:
                seller_id = query.get("sellerId") or query.get("seller_id")

        clauses = []
        params = {}
        if status is not None:
            clauses.append("status = :status")
            params["status"] = status
        if user_id is not None:
            clauses.append("user_id = :uid")
            params["uid"] = str(user_id)
        if order_id is not None:
            clauses.append("order_id = :oid")
            params["oid"] = str(order_id)
        if valet_id is not None:
            clauses.append("valet_id = :vid")
            params["vid"] = str(valet_id)
        if seller_id is not None:
            clauses.append("seller_id = :sid")
            params["sid"] = str(seller_id)

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: 'ReturnRequestInternalCreate') -> 'ReturnRequestInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.return_id is not None:
            cols.append("return_id")
            params["s_returnId"] = data.return_id

        if data.order_id is not None:
            cols.append("order_id")
            params["s_orderId"] = data.order_id

        if data.user_id is not None:
            cols.append("user_id")
            params["s_userId"] = data.user_id

        if data.payment_method is not None:
            cols.append("payment_method")
            params["s_paymentMethod"] = data.payment_method

        if data.upi_payment_screenshot is not None:
            cols.append("upi_payment_screenshot")
            params["s_upiPaymentScreenshot"] = data.upi_payment_screenshot

        if data.notes is not None:
            cols.append("notes")
            params["s_notes"] = data.notes

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status

        if data.valet_id is not None:
            cols.append("valet_id")
            params["s_valetId"] = data.valet_id

        if data.seller_id is not None:
            cols.append("seller_id")
            params["s_sellerId"] = data.seller_id

        if data.delivery_slot_id is not None:
            cols.append("delivery_slot_id")
            params["s_deliverySlotId"] = data.delivery_slot_id

        if data.delivery_slot_config_id is not None:
            cols.append("delivery_slot_config_id")
            params["s_deliverySlotConfigId"] = data.delivery_slot_config_id

        if data.delivery_slot_date is not None:
            cols.append("delivery_slot_date")
            params["s_deliverySlotDate"] = data.delivery_slot_date

        if data.pending_valet_id is not None:
            cols.append("pending_valet_id")
            params["s_pendingValetId"] = data.pending_valet_id

        if data.valet_assigned_at is not None:
            cols.append("valet_assigned_at")
            params["s_valetAssignedAt"] = data.valet_assigned_at

        if data.valet_cascade_count is not None:
            cols.append("valet_cascade_count")
            params["s_valetCascadeCount"] = data.valet_cascade_count

        if data.delivery_charge is not None:
            cols.append("delivery_charge")
            params["s_deliveryCharge"] = data.delivery_charge

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['return_id', 'order_id', 'user_id', 'payment_method', 'upi_payment_screenshot', 'notes', 'status', 'valet_id', 'seller_id', 'delivery_slot_id', 'delivery_slot_config_id', 'delivery_slot_date', 'pending_valet_id', 'valet_assigned_at', 'valet_cascade_count', 'delivery_charge'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'ReturnRequestInternalUpdate') -> 'ReturnRequestInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}
        
        field_map = {
            "return_id": "return_id",
            "order_id": "order_id",
            "user_id": "user_id",
            "payment_method": "payment_method",
            "upi_payment_screenshot": "upi_payment_screenshot",
            "notes": "notes",
            "status": "status",
            "valet_id": "valet_id",
            "seller_id": "seller_id",
            "delivery_slot_id": "delivery_slot_id",
            "delivery_slot_config_id": "delivery_slot_config_id",
            "delivery_slot_date": "delivery_slot_date",
            "pending_valet_id": "pending_valet_id",
            "valet_assigned_at": "valet_assigned_at",
            "valet_cascade_count": "valet_cascade_count",
            "delivery_charge": "delivery_charge"
        }
        
        if hasattr(data, 'model_dump'):
            dump = data.model_dump(exclude_unset=True)
            for k, v in dump.items():
                if k in field_map:
                    updates.append(f"{field_map[k]} = :s_{k}")
                    params[f"s_{k}"] = v
                    
        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(str(id))

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid OR return_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False

            await session.execute(text("DELETE FROM sj_return_request_items WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_return_valet_declines WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> 'ReturnRequestInternal':
        from app.models.daos_flat import ReturnRequestInternal
        return ReturnRequestInternal(
            id=str(r.id),
            return_id=r.return_id,
            order_id=r.order_id,
            user_id=r.user_id,
            payment_method=r.payment_method,
            upi_payment_screenshot=r.upi_payment_screenshot,
            notes=r.notes,
            status=r.status,
            valet_id=r.valet_id,
            seller_id=r.seller_id,
            delivery_slot_id=r.delivery_slot_id,
            delivery_slot_config_id=r.delivery_slot_config_id,
            delivery_slot_date=r.delivery_slot_date,
            pending_valet_id=r.pending_valet_id,
            valet_assigned_at=r.valet_assigned_at,
            valet_cascade_count=int(r.valet_cascade_count) if r.valet_cascade_count is not None else None,
            delivery_charge=float(r.delivery_charge) if r.delivery_charge is not None else None,
            items=children.get("items", []),
            valet_decline_history=children.get("valetDeclineHistory", []),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_items = text(f"SELECT parent_id, product_id, quantity, reason FROM sj_return_request_items WHERE parent_id IN ({id_list})")
        res_items = await session.execute(q_items)
        rows_items = res_items.fetchall()

        for r in rows_items:
            if "items" not in c_map[r.parent_id]:
                c_map[r.parent_id]["items"] = []
            obj = {}

            obj["product_id"] = r[1]
            obj["quantity"] = r[2]
            obj["reason"] = r[3]
            c_map[r.parent_id]["items"].append(obj)

        q_valetDeclineHistory = text(f"SELECT parent_id, valet_id, reason FROM sj_return_valet_declines WHERE parent_id IN ({id_list})")
        res_valetDeclineHistory = await session.execute(q_valetDeclineHistory)
        rows_valetDeclineHistory = res_valetDeclineHistory.fetchall()

        for r in rows_valetDeclineHistory:
            if "valetDeclineHistory" not in c_map[r.parent_id]:
                c_map[r.parent_id]["valetDeclineHistory"] = []
            obj = {}

            obj["valet_id"] = r[1]
            obj["reason"] = r[2]
            c_map[r.parent_id]["valetDeclineHistory"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):
        fields = data.model_fields_set if hasattr(data, 'model_fields_set') else set(dir(data))
        
        if 'items' in fields:
            await session.execute(text(f"DELETE FROM sj_return_request_items WHERE parent_id = :id"), {"id": row_id})
            child_list = data.items if hasattr(data, 'items') else []
            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = getattr(item, 'product_id', None)
                    p["v1"] = getattr(item, 'quantity', None)
                    p["v2"] = getattr(item, 'reason', None)
                    await session.execute(text(f"INSERT INTO sj_return_request_items (parent_id, product_id, quantity, reason) VALUES (:id, :v0, :v1, :v2)"), p)

        if 'valet_decline_history' in fields:
            await session.execute(text(f"DELETE FROM sj_return_valet_declines WHERE parent_id = :id"), {"id": row_id})
            child_list = data.valet_decline_history if hasattr(data, 'valet_decline_history') else []
            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = getattr(item, 'valet_id', None)
                    p["v1"] = getattr(item, 'reason', None)
                    p["v2"] = getattr(item, 'declined_at', None)
                    await session.execute(text(f"INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason) VALUES (:id, :v0, :v1)"), p)
