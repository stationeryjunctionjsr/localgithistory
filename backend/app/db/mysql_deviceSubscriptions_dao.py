from typing import Optional, List, Union
from datetime import datetime, timezone
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
        
    async def findById(self, id: int) -> Optional[DeviceSubscriptionInternal]:
        if not id:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": id}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            keys = await self._fetch_keys(session, row.id)
            return self._map_to_schema(row, keys)

    async def findOne(
        self,
        id: Optional[int] = None,
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
            parent_ids = [r.id for r in rows]
            id_list = ",".join(str(i) for i in parent_ids)
            keys_res = await session.execute(
                text(f"SELECT parent_id, key_name, key_value FROM sj_device_keys WHERE parent_id IN ({id_list}) ORDER BY id ASC")
            )
            all_key_rows = keys_res.fetchall()
            return [
                self._map_to_schema(
                    r,
                    keys=[
                        DeviceKeyInternal(key=kr.key_name, value=kr.key_value)
                        for kr in all_key_rows
                        if kr.parent_id == r.id
                    ],
                )
                for r in rows
            ]

    async def create(self, data: DeviceSubscriptionInternalCreate) -> DeviceSubscriptionInternal:
        factory = self._factory()
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        val_placeholders = [":c", ":u"]
        params = {"c": now, "u": now}

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
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: DeviceSubscriptionInternalUpdate) -> Optional[DeviceSubscriptionInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"pk": id, "u": now_utc()}

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
            upd_where = "id = :pk"

            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)
            await self._replace_children(session, id, update_data)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            params = {"id": id}

            await session.execute(text("DELETE FROM sj_device_keys WHERE parent_id = :id"), params)
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, keys: Optional[List[DeviceKeyInternal]] = None) -> DeviceSubscriptionInternal:
        return DeviceSubscriptionInternal(
            id=r.id,
            user_id=r.user_id,
            endpoint=r.endpoint,
            expo_token=r.expo_token,
            keys=keys if keys else None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_keys(self, session, parent_id: int) -> List[DeviceKeyInternal]:
        res = await session.execute(
            text("SELECT key_name, key_value FROM sj_device_keys WHERE parent_id = :pid ORDER BY id ASC"),
            {"pid": parent_id},
        )
        return [
            DeviceKeyInternal(key=r.key_name, value=r.key_value)
            for r in res.fetchall()
        ]

    async def _replace_children(self, session, row_id: int, data: Union[DeviceSubscriptionInternalCreate, DeviceSubscriptionInternalUpdate]):
        if data.keys is not None:
            await session.execute(text("DELETE FROM sj_device_keys WHERE parent_id = :id"), {"id": row_id})
            if data.keys:
                params = [{"id": row_id, "v0": item.key, "v1": item.value} for item in data.keys]
                await session.execute(
                    text("INSERT INTO sj_device_keys (parent_id, key_name, key_value) VALUES (:id, :v0, :v1)"),
                    params,
                )
