from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import ContactInternal
from app.models.daos_flat import ContactInternalCreate, ContactInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLContactsDAO:
    def __init__(self):
        self.table_name = "sj_contacts"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

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
            
            query_map = {'email': 'email', 'description': 'description', 'is_active': 'is_active', 'display_order': 'display_order'}
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
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'email': 'email', 'description': 'description', 'is_active': 'is_active', 'display_order': 'display_order'}
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

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.email is not None:
            cols.append("email")
            params["s_email"] = data.email

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        if data.display_order is not None:
            cols.append("display_order")
            params["s_display_order"] = data.display_order

        if data.social_media is not None:
            cols.append("social_media")
            import json
            params["s_social_media"] = json.dumps({
                "instagram": data.social_media.instagram,
                "facebook": data.social_media.facebook,
                "twitter": data.social_media.twitter,
                "whatsapp": data.social_media.whatsapp,
                "youtube": data.social_media.youtube,
                "linkedin": data.social_media.linkedin
            })

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['email', 'description', 'is_active', 'display_order', 'social_media'] if f"s_{k}" in params])
        
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

        if data.email is not None:
            updates.append("email = :s_email")
            params["s_email"] = data.email

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

        if data.display_order is not None:
            updates.append("display_order = :s_displayOrder")
            params["s_display_order"] = data.display_order

        if data.social_media is not None:
            updates.append("social_media = :s_socialMedia")
            import json
            params["s_social_media"] = json.dumps({
                "instagram": data.social_media.instagram,
                "facebook": data.social_media.facebook,
                "twitter": data.social_media.twitter,
                "whatsapp": data.social_media.whatsapp,
                "youtube": data.social_media.youtube,
                "linkedin": data.social_media.linkedin
            })

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

            await session.execute(text(f"DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": pk})

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
        import json
        c = ContactInternal.model_validate(r)
        if getattr(r, "social_media", None):
            try:
                c.social_media = json.loads(r.social_media)
            except:
                pass
        for k, v in children.items():
            setattr(c, k, v)
        return c

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_addresses = text(f"SELECT parent_id, address FROM sj_contact_addresses WHERE parent_id IN ({id_list})")
        res_addresses = await session.execute(q_addresses)
        rows_addresses = res_addresses.fetchall()

        for r in rows_addresses:
            if "addresses" not in c_map[r.parent_id]:
                c_map[r.parent_id]["addresses"] = []
            c_map[r.parent_id]["addresses"].append(r[1])

        q_phone_numbers = text(f"SELECT parent_id, phone FROM sj_contact_phones WHERE parent_id IN ({id_list})")
        res_phone_numbers = await session.execute(q_phone_numbers)
        rows_phone_numbers = res_phone_numbers.fetchall()

        for r in rows_phone_numbers:
            if "phone_numbers" not in c_map[r.parent_id]:
                c_map[r.parent_id]["phone_numbers"] = []
            c_map[r.parent_id]["phone_numbers"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.addresses is not None:
            await session.execute(text(f"DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": row_id})
            child_list = data.addresses or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_contact_addresses (parent_id, address) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.phone_numbers is not None:
            await session.execute(text(f"DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": row_id})
            child_list = data.phone_numbers or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_contact_phones (parent_id, phone) VALUES (:id, :v)"), {"id": row_id, "v": item})

