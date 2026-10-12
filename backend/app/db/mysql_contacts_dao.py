from typing import Optional, List, Union, Tuple, Any
from datetime import datetime, timezone
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
        
    async def findById(self, id: int) -> Optional[ContactInternal]:
        if not id:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            address_rows, phone_rows = await self._fetch_children(session, [row.id])
            return self._map_to_schema(
                row,
                addresses=[str(a.address) for a in address_rows if a.parent_id == row.id],
                phone_numbers=[str(p.phone) for p in phone_rows if p.parent_id == row.id],
            )

    async def findOne(
        self,
        id: Optional[int] = None,
        email: Optional[str] = None,
    ) -> Optional[ContactInternal]:
        if id:
            return await self.findById(id)
        if email:
            async with self._factory()() as session:
                q = text(f"SELECT * FROM {self.TABLE} WHERE email = :email LIMIT 1")
                result = await session.execute(q, {"email": email})
                row = result.fetchone()
                if not row:
                    return None
                address_rows, phone_rows = await self._fetch_children(session, [int(row.id)])
                return self._map_to_schema(
                    row,
                    addresses=[str(a.address) for a in address_rows if int(a.parent_id) == int(row.id)],
                    phone_numbers=[str(p.phone) for p in phone_rows if int(p.parent_id) == int(row.id)],
                )
        all_contacts = await self.findAll()
        return all_contacts[0] if all_contacts else None
            
    async def findAll(
        self,
        is_active: Optional[bool] = None,
    ) -> List[ContactInternal]:
        async with self._factory()() as session:
            clauses = []
            params = {}

            if is_active is not None:
                clauses.append("is_active = :act")
                params["act"] = 1 if is_active else 0

            sql = f"SELECT * FROM {self.TABLE}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY display_order ASC, id ASC"
                    
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
                
            row_ids = [int(r.id) for r in rows]
            address_rows, phone_rows = await self._fetch_children(session, row_ids)
            return [
                self._map_to_schema(
                    r,
                    addresses=[str(a.address) for a in address_rows if int(a.parent_id) == int(r.id)],
                    phone_numbers=[str(p.phone) for p in phone_rows if int(p.parent_id) == int(r.id)],
                )
                for r in rows
            ]

    async def create(self, data: ContactInternalCreate) -> ContactInternal:
        factory = self._factory()
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        val_placeholders = [":c", ":u"]
        params = {"c": now, "u": now}

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
            params["social_media"] = data.social_media.model_dump_json()

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: ContactInternalUpdate) -> Optional[ContactInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

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
            params["social_media"] = update_data.social_media.model_dump_json()

        upd_sql = ", ".join(updates)
        params["pk"] = id

        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :pk"), params)
            await self._replace_children(session, id, update_data)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": id})
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :pk"),
                {"pk": id},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(
        self,
        r,
        addresses: List[str],
        phone_numbers: List[str],
    ) -> ContactInternal:
        social = None
        if r.social_media:
            try:
                social = SocialMedia.model_validate_json(r.social_media)
            except Exception:
                social = None

        return ContactInternal(
            id=str(r.id),
            email=r.email,
            description=r.description,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            display_order=int(r.display_order) if r.display_order is not None else 0,
            addresses=addresses,
            phone_numbers=phone_numbers,
            social_media=social,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(
        self, session, ids: List[int]
    ) -> Tuple[List[Any], List[Any]]:
        if not ids:
            return [], []
            
        id_list = ",".join(map(str, ids))

        q_addresses = text(f"SELECT parent_id, address FROM sj_contact_addresses WHERE parent_id IN ({id_list})")
        res_addresses = await session.execute(q_addresses)

        q_phones = text(f"SELECT parent_id, phone FROM sj_contact_phones WHERE parent_id IN ({id_list})")
        res_phones = await session.execute(q_phones)

        return res_addresses.fetchall(), res_phones.fetchall()

    async def _replace_children(self, session, row_id: int, data: Union[ContactInternalCreate, ContactInternalUpdate]):
        if data.addresses is not None:
            await session.execute(text("DELETE FROM sj_contact_addresses WHERE parent_id = :id"), {"id": row_id})
            for item in data.addresses:
                await session.execute(
                    text("INSERT INTO sj_contact_addresses (parent_id, address) VALUES (:id, :v)"),
                    {"id": row_id, "v": item}
                )

        if data.phone_numbers is not None:
            await session.execute(text("DELETE FROM sj_contact_phones WHERE parent_id = :id"), {"id": row_id})
            for item in data.phone_numbers:
                await session.execute(
                    text("INSERT INTO sj_contact_phones (parent_id, phone) VALUES (:id, :v)"),
                    {"id": row_id, "v": item}
                )
