from typing import Optional, Dict, List, Any
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
        
    async def findById(self, id: str) -> Optional['ReturnRequestInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['ReturnRequestInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'returnId': 'return_id', 'orderId': 'order_id', 'userId': 'user_id', 'paymentMethod': 'payment_method', 'upiPaymentScreenshot': 'upi_payment_screenshot', 'notes': 'notes', 'status': 'status', 'valetId': 'valet_id', 'sellerId': 'seller_id', 'deliverySlotId': 'delivery_slot_id', 'deliverySlotConfigId': 'delivery_slot_config_id', 'deliverySlotDate': 'delivery_slot_date', 'pendingValetId': 'pending_valet_id', 'valetAssignedAt': 'valet_assigned_at', 'valetCascadeCount': 'valet_cascade_count', 'deliveryCharge': 'delivery_charge'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map[k] if k in query_map else k
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List['ReturnRequestInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'returnId': 'return_id', 'orderId': 'order_id', 'userId': 'user_id', 'paymentMethod': 'payment_method', 'upiPaymentScreenshot': 'upi_payment_screenshot', 'notes': 'notes', 'status': 'status', 'valetId': 'valet_id', 'sellerId': 'seller_id', 'deliverySlotId': 'delivery_slot_id', 'deliverySlotConfigId': 'delivery_slot_config_id', 'deliverySlotDate': 'delivery_slot_date', 'pendingValetId': 'pending_valet_id', 'valetAssignedAt': 'valet_assigned_at', 'valetCascadeCount': 'valet_cascade_count', 'deliveryCharge': 'delivery_charge'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map[k] if k in query_map else k
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
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

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:

            await session.execute(text(f"DELETE FROM sj_return_request_items WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_return_valet_declines WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> 'ReturnRequestInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'ReturnRequestInternal':
        d = dict(r._mapping)
        if "items" in children:
            d["items"] = children["items"]
        if "valetDeclineHistory" in children:
            d["valet_decline_history"] = children["valetDeclineHistory"]
        return ReturnRequestInternal.model_validate(d)

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
