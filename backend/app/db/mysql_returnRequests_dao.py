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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"{self.table_name}{suffix}"

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional[Any]:
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
                db_col = query_map.get(k, k)
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
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
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
                    db_col = query_map.get(k, k)
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

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.returnId is not None:
            cols.append("return_id")
            params["s_returnId"] = data.returnId

        if data.orderId is not None:
            cols.append("order_id")
            params["s_orderId"] = data.orderId

        if data.userId is not None:
            cols.append("user_id")
            params["s_userId"] = data.userId

        if data.paymentMethod is not None:
            cols.append("payment_method")
            params["s_paymentMethod"] = data.paymentMethod

        if data.upiPaymentScreenshot is not None:
            cols.append("upi_payment_screenshot")
            params["s_upiPaymentScreenshot"] = data.upiPaymentScreenshot

        if data.notes is not None:
            cols.append("notes")
            params["s_notes"] = data.notes

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status

        if data.valetId is not None:
            cols.append("valet_id")
            params["s_valetId"] = data.valetId

        if data.sellerId is not None:
            cols.append("seller_id")
            params["s_sellerId"] = data.sellerId

        if data.deliverySlotId is not None:
            cols.append("delivery_slot_id")
            params["s_deliverySlotId"] = data.deliverySlotId

        if data.deliverySlotConfigId is not None:
            cols.append("delivery_slot_config_id")
            params["s_deliverySlotConfigId"] = data.deliverySlotConfigId

        if data.deliverySlotDate is not None:
            cols.append("delivery_slot_date")
            params["s_deliverySlotDate"] = data.deliverySlotDate

        if data.pendingValetId is not None:
            cols.append("pending_valet_id")
            params["s_pendingValetId"] = data.pendingValetId

        if data.valetAssignedAt is not None:
            cols.append("valet_assigned_at")
            params["s_valetAssignedAt"] = data.valetAssignedAt

        if data.valetCascadeCount is not None:
            cols.append("valet_cascade_count")
            params["s_valetCascadeCount"] = data.valetCascadeCount

        if data.deliveryCharge is not None:
            cols.append("delivery_charge")
            params["s_deliveryCharge"] = data.deliveryCharge

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['returnId', 'orderId', 'userId', 'paymentMethod', 'upiPaymentScreenshot', 'notes', 'status', 'valetId', 'sellerId', 'deliverySlotId', 'deliverySlotConfigId', 'deliverySlotDate', 'pendingValetId', 'valetAssignedAt', 'valetCascadeCount', 'deliveryCharge'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, data: Any) -> Any:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.returnId is not None:
            updates.append("return_id = :s_returnId")
            params["s_returnId"] = data.returnId

        if data.orderId is not None:
            updates.append("order_id = :s_orderId")
            params["s_orderId"] = data.orderId

        if data.userId is not None:
            updates.append("user_id = :s_userId")
            params["s_userId"] = data.userId

        if data.paymentMethod is not None:
            updates.append("payment_method = :s_paymentMethod")
            params["s_paymentMethod"] = data.paymentMethod

        if data.upiPaymentScreenshot is not None:
            updates.append("upi_payment_screenshot = :s_upiPaymentScreenshot")
            params["s_upiPaymentScreenshot"] = data.upiPaymentScreenshot

        if data.notes is not None:
            updates.append("notes = :s_notes")
            params["s_notes"] = data.notes

        if data.status is not None:
            updates.append("status = :s_status")
            params["s_status"] = data.status

        if data.valetId is not None:
            updates.append("valet_id = :s_valetId")
            params["s_valetId"] = data.valetId

        if data.sellerId is not None:
            updates.append("seller_id = :s_sellerId")
            params["s_sellerId"] = data.sellerId

        if data.deliverySlotId is not None:
            updates.append("delivery_slot_id = :s_deliverySlotId")
            params["s_deliverySlotId"] = data.deliverySlotId

        if data.deliverySlotConfigId is not None:
            updates.append("delivery_slot_config_id = :s_deliverySlotConfigId")
            params["s_deliverySlotConfigId"] = data.deliverySlotConfigId

        if data.deliverySlotDate is not None:
            updates.append("delivery_slot_date = :s_deliverySlotDate")
            params["s_deliverySlotDate"] = data.deliverySlotDate

        if data.pendingValetId is not None:
            updates.append("pending_valet_id = :s_pendingValetId")
            params["s_pendingValetId"] = data.pendingValetId

        if data.valetAssignedAt is not None:
            updates.append("valet_assigned_at = :s_valetAssignedAt")
            params["s_valetAssignedAt"] = data.valetAssignedAt

        if data.valetCascadeCount is not None:
            updates.append("valet_cascade_count = :s_valetCascadeCount")
            params["s_valetCascadeCount"] = data.valetCascadeCount

        if data.deliveryCharge is not None:
            updates.append("delivery_charge = :s_deliveryCharge")
            params["s_deliveryCharge"] = data.deliveryCharge

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(id)

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

    async def deleteMany(self, query: Dict) -> Any:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> Any:
        rm = r._mapping
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()

        out["returnId"] = rm["return_id"]
        out["orderId"] = rm["order_id"]
        out["userId"] = rm["user_id"]
        out["paymentMethod"] = rm["payment_method"]
        out["upiPaymentScreenshot"] = rm["upi_payment_screenshot"]
        out["notes"] = rm["notes"]
        out["status"] = rm["status"]
        out["valetId"] = rm["valet_id"]
        out["sellerId"] = rm["seller_id"]
        out["deliverySlotId"] = rm["delivery_slot_id"]
        out["deliverySlotConfigId"] = rm["delivery_slot_config_id"]
        out["deliverySlotDate"] = rm["delivery_slot_date"]
        out["pendingValetId"] = rm["pending_valet_id"]
        out["valetAssignedAt"] = rm["valet_assigned_at"]
        out["valetCascadeCount"] = rm["valet_cascade_count"]
        out["deliveryCharge"] = rm["delivery_charge"]
        for k, v in children.items():
            out[k] = v
            
        return ReturnRequestInternal(**out)

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

            obj["productId"] = r[1]
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

            obj["valetId"] = r[1]
            obj["reason"] = r[2]
            c_map[r.parent_id]["valetDeclineHistory"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.items is not None:
            await session.execute(text(f"DELETE FROM sj_return_request_items WHERE parent_id = :id"), {"id": row_id})
            child_list = data.items or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.productId
                    p["v1"] = item.quantity
                    p["v2"] = item.reason
                    await session.execute(text(f"INSERT INTO sj_return_request_items (parent_id, product_id, quantity, reason) VALUES (:id, :v0, :v1, :v2)"), p)

        if data.valetDeclineHistory is not None:
            await session.execute(text(f"DELETE FROM sj_return_valet_declines WHERE parent_id = :id"), {"id": row_id})
            child_list = data.valetDeclineHistory or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.valetId
                    p["v1"] = item.reason
                    await session.execute(text(f"INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason) VALUES (:id, :v0, :v1)"), p)
