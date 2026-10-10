from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import ContactInternal, ContactInternalCreate, ContactInternalUpdate, SocialMedia

def now_utc():
    return datetime.now(timezone.utc)

class MySQLContactsDAO:
    def __init__(self):
        self.table_name = "sj_contacts"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional[ContactInternal]:
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": pk})
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [pk])
            return self._map_to_schema(row, children_map.get(pk, {}))

    async def findOne(self, query: Optional[dict] = None, **kwargs) -> Optional[ContactInternal]:
        params_dict = {}
        if query:
            params_dict.update(query)
        params_dict.update(kwargs)
        if not params_dict:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}
            for k, v in params_dict.items():
                if k in ("_id", "id"):
                    conditions.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else v
                elif k in ("externalId", "external_id"):
                    conditions.append("external_id = :external_id")
                    params["external_id"] = str(v)
                elif k in ("isActive", "is_active"):
                    conditions.append("is_active = :is_active")
                    params["is_active"] = 1 if v else 0
                elif k in ("displayOrder", "display_order"):
                    conditions.append("display_order = :display_order")
                    params["display_order"] = int(v)
                elif k == "email":
                    conditions.append("email = :email")
                    params["email"] = str(v)
                else:
                    conditions.append(f"{k} = :{k}")
                    params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[dict] = None, is_active: Optional[bool] = None) -> List[ContactInternal]:
        if is_active is None and query:
            val = query.get("isActive") if "isActive" in query else query.get("is_active")
            if val is not None:
                is_active = bool(val)

        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}

            if is_active is not None:
                conditions.append("is_active = :is_active")
                params["is_active"] = 1 if is_active else 0

            if query:
                for k, v in query.items():
                    if k in ("isActive", "is_active"):
                        continue
                    if k in ("_id", "id"):
                        conditions.append("id = :id")
                        params["id"] = int(v) if str(v).isdigit() else v
                    elif k in ("externalId", "external_id"):
                        conditions.append("external_id = :external_id")
                        params["external_id"] = str(v)
                    elif k in ("displayOrder", "display_order"):
                        conditions.append("display_order = :display_order")
                        params["display_order"] = int(v)
                    elif k == "email":
                        conditions.append("email = :email")
                        params["email"] = str(v)
                    else:
                        conditions.append(f"{k} = :{k}")
                        params[k] = v
                        
            sql = f"SELECT * FROM {self.TABLE}"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: ContactInternalCreate) -> ContactInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params: Dict[str, Any] = {"eid": external_id, "c": now, "u": now}

        if data.email is not None:
            cols.append("email")
            val_placeholders.append(":email")
            params["email"] = data.email

        if data.description is not None:
            cols.append("description")
            val_placeholders.append(":description")
            params["description"] = data.description

        if data.is_active is not None:
            cols.append("is_active")
            val_placeholders.append(":is_active")
            params["is_active"] = 1 if data.is_active else 0

        if data.display_order is not None:
            cols.append("display_order")
            val_placeholders.append(":display_order")
            params["display_order"] = data.display_order

        if data.social_media is not None:
            cols.append("social_media")
            val_placeholders.append(":social_media")
            params["social_media"] = json.dumps(data.social_media.model_dump())

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
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: ContactInternalUpdate) -> ContactInternal:
        factory = self._factory()
        updates = ["updated_at = :u"]
        pk = int(id) if str(id).isdigit() else None
        params: Dict[str, Any] = {"id": pk, "u": now_utc()}

        if update_data.email is not None:
            updates.append("email = :email")
            params["email"] = update_data.email

        if update_data.description is not None:
            updates.append("description = :description")
            params["description"] = update_data.description

        if update_data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        if update_data.display_order is not None:
            updates.append("display_order = :display_order")
            params["display_order"] = update_data.display_order

        if update_data.social_media is not None:
            updates.append("social_media = :social_media")
            params["social_media"] = json.dumps(update_data.social_media.model_dump())

        upd_sql = ", ".join(updates)
        async with factory() as session:
            if pk is not None:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, pk, update_data)
                await session.commit()
                
        return await self.findById(str(id))

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return False
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> ContactInternal:
        social = None
        if getattr(r, "social_media", None):
            try:
                raw_social = r.social_media
                if isinstance(raw_social, str):
                    raw_social = json.loads(raw_social)
                if isinstance(raw_social, dict):
                    social = SocialMedia.model_validate(raw_social)
            except Exception:
                social = None

        return ContactInternal(
            id=str(r.id),
            external_id=getattr(r, "external_id", None),
            email=getattr(r, "email", None),
            description=getattr(r, "description", None),
            is_active=bool(r.is_active) if getattr(r, "is_active", None) is not None else True,
            display_order=int(r.display_order) if getattr(r, "display_order", None) is not None else 0,
            addresses=children.get("addresses", []),
            phone_numbers=children.get("phone_numbers", []),
            social_media=social,
            created_at=getattr(r, "created_at", None),
            updated_at=getattr(r, "updated_at", None),
        )

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
            c_map[r.parent_id]["addresses"].append(r.address)

        q_phone_numbers = text(f"SELECT parent_id, phone FROM sj_contact_phones WHERE parent_id IN ({id_list})")
        res_phone_numbers = await session.execute(q_phone_numbers)
        rows_phone_numbers = res_phone_numbers.fetchall()

        for r in rows_phone_numbers:
            if "phone_numbers" not in c_map[r.parent_id]:
                c_map[r.parent_id]["phone_numbers"] = []
            c_map[r.parent_id]["phone_numbers"].append(r.phone)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):
        if hasattr(data, "addresses") and data.addresses is not None:
            await session.execute(text("DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": row_id})
            for item in data.addresses:
                await session.execute(
                    text("INSERT INTO sj_contact_addresses (parent_id, address) VALUES (:id, :v)"),
                    {"id": row_id, "v": item}
                )

        if hasattr(data, "phone_numbers") and data.phone_numbers is not None:
            await session.execute(text("DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": row_id})
            for item in data.phone_numbers:
                await session.execute(
                    text("INSERT INTO sj_contact_phones (parent_id, phone) VALUES (:id, :v)"),
                    {"id": row_id, "v": item}
                )
