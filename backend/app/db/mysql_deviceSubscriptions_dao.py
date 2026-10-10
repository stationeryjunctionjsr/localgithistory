from typing import Optional, Dict, List, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import (
    DeviceSubscriptionInternal,
    DeviceSubscriptionInternalCreate,
    DeviceSubscriptionInternalUpdate,
    DeviceKeyInternal,
)

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeviceSubscriptionsDAO:
    def __init__(self):
        self.table_name = "sj_device_subscriptions"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[DeviceSubscriptionInternal]:
        if not id:
            return None
        async with self._factory()() as session:
            if str(id).isdigit():
                q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
                params = {"id": int(id)}
            else:
                q = text(f"SELECT * FROM {self.TABLE} WHERE external_id = :id LIMIT 1")
                params = {"id": str(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id)))

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        expo_token: Optional[str] = None,
    ) -> Optional[DeviceSubscriptionInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(user_id=user_id, endpoint=endpoint, expo_token=expo_token, limit=1)
        return results[0] if results else None

    async def findAll(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        expo_token: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[DeviceSubscriptionInternal]:
        clauses = []
        params = {}
        if user_id is not None:
            clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if endpoint is not None:
            clauses.append("endpoint = :endpoint")
            params["endpoint"] = endpoint
        if expo_token is not None:
            clauses.append("expo_token = :expo_token")
            params["expo_token"] = expo_token

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        limit_sql = f" LIMIT {int(limit)}" if limit else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC{limit_sql}"

        async with self._factory()() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id))) for r in rows]

    async def create(self, data: DeviceSubscriptionInternalCreate) -> DeviceSubscriptionInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.user_id is not None:
            cols.append("user_id")
            val_placeholders.append(":user_id")
            params["user_id"] = data.user_id

        if data.endpoint is not None:
            cols.append("endpoint")
            val_placeholders.append(":endpoint")
            params["endpoint"] = data.endpoint

        if data.expo_token is not None:
            cols.append("expo_token")
            val_placeholders.append(":expo_token")
            params["expo_token"] = data.expo_token

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: DeviceSubscriptionInternalUpdate) -> Optional[DeviceSubscriptionInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.user_id is not None:
            updates.append("user_id = :user_id")
            params["user_id"] = update_data.user_id

        if update_data.endpoint is not None:
            updates.append("endpoint = :endpoint")
            params["endpoint"] = update_data.endpoint

        if update_data.expo_token is not None:
            updates.append("expo_token = :expo_token")
            params["expo_token"] = update_data.expo_token

        upd_sql = ", ".join(updates)
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                upd_where = "id = :pk"
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return None
                upd_where = "id = :pk"
            params["pk"] = pk

            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)
            await self._replace_children(session, pk, update_data)
            await session.commit()
                
        return await self.findById(pk)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                del_where = "id = :pk"
                params = {"pk": pk}
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False
                del_where = "id = :pk"
                params = {"pk": pk}

            await session.execute(text("DELETE FROM sj_device_keys WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {del_where}"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, keys: Optional[List[DeviceKeyInternal]] = None) -> DeviceSubscriptionInternal:
        return DeviceSubscriptionInternal(
            id=str(r.id),
            external_id=r.external_id,
            user_id=r.user_id,
            endpoint=r.endpoint,
            expo_token=r.expo_token,
            keys=keys if keys else None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[DeviceKeyInternal]]:
        c_map: Dict[int, List[DeviceKeyInternal]] = {rid: [] for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(str(int(i)) for i in ids)
        res = await session.execute(
            text(f"SELECT parent_id, key_name, key_value FROM sj_device_keys WHERE parent_id IN ({id_list})")
        )
        for r in res.fetchall():
            c_map[r.parent_id].append(DeviceKeyInternal(key=r.key_name, value=r.key_value))

        return c_map

    async def _replace_children(self, session, row_id: int, data: Union[DeviceSubscriptionInternalCreate, DeviceSubscriptionInternalUpdate]):
        if data.keys is not None:
            await session.execute(text("DELETE FROM sj_device_keys WHERE parent_id = :id"), {"id": row_id})
            for item in data.keys:
                await session.execute(
                    text("INSERT INTO sj_device_keys (parent_id, key_name, key_value) VALUES (:id, :v0, :v1)"),
                    {"id": row_id, "v0": item.key, "v1": item.value},
                )
