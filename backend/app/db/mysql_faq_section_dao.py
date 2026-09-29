import secrets
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.utils.time import now_utc
from app.models.faq_section import FaqSectionInternalCreate, FaqSectionInternalUpdate, FaqSectionResponse, FaqItem

class MySQLFaqSectionDAO:
    TABLE = "sj_faq_sections"

    async def _fetch_items(self, section_id: str) -> List[FaqItem]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT question, answer FROM sj_faq_items WHERE section_id = :sid ORDER BY id ASC"),
                {"sid": section_id},
            )
            rows = result.fetchall()
            return [FaqItem(question=r.question, answer=r.answer) for r in rows]

    async def _save_items(self, section_id: str, items: List[FaqItem]):
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            await session.execute(text("DELETE FROM sj_faq_items WHERE section_id = :sid"), {"sid": section_id})
            if items:
                params = [
                    {"sid": section_id, "q": (item.question if item.question is not None else ""), "a": (item.answer if item.answer is not None else "")} for item in items
                ]
                await session.execute(
                    text("INSERT INTO sj_faq_items (section_id, question, answer) VALUES (:sid, :q, :a)"), params
                )
            await session.commit()

    async def _map_row(self, row) -> FaqSectionResponse:
        return FaqSectionResponse(
            _id=str(row.id),
            externalId=row.external_id,
            title=row.title,
            orderIndex=row.order_index,
            isActive=bool(row.is_active),
            icon=row.icon,
            createdAt=str(row.created_at) if row.created_at else None,
            updatedAt=str(row.updated_at) if row.updated_at else None,
            items=await self._fetch_items(row.external_id)
        )

    async def findById(self, id: str) -> Optional[FaqSectionResponse]:
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        async with SessionLocal() as session:
            res = await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            row = res.fetchone()
            if not row:
                return None
            return await self._map_row(row)

    async def findAll(self) -> List[FaqSectionResponse]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            res = await session.execute(text(f"SELECT * FROM {self.TABLE}"))
            return [await self._map_row(row) for row in res.fetchall()]

    async def create(self, data: FaqSectionInternalCreate) -> FaqSectionResponse:
        SessionLocal = get_async_session_factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        async with SessionLocal() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} (external_id, created_at, updated_at, title, order_index, is_active, icon) VALUES (:eid, :c, :u, :title, :oi, :ia, :ic)"),
                {
                    "eid": ext_id, "c": now, "u": now,
                    "title": data.title,
                    "oi": data.orderIndex,
                    "ia": 1 if data.isActive else 0,
                    "ic": data.icon
                }
            )
            res = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})
            new_id = res.scalar()
            await session.commit()
            
        await self._save_items(ext_id, data.items or [])
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: FaqSectionInternalUpdate) -> Optional[FaqSectionResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        now = now_utc()
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        if update_data.title is not None:
            updates.append("title = :title")
            params["title"] = update_data.title
        if update_data.orderIndex is not None:
            updates.append("order_index = :oi")
            params["oi"] = update_data.orderIndex
        if update_data.isActive is not None:
            updates.append("is_active = :ia")
            params["ia"] = 1 if update_data.isActive else 0
        if update_data.icon is not None:
            updates.append("icon = :ic")
            params["ic"] = update_data.icon
            
        async with SessionLocal() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {','.join(updates)} WHERE id = :id"),
                params
            )
            await session.commit()
            
        if update_data.items is not None:
            await self._save_items(existing.externalId, update_data.items)
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        async with SessionLocal() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            await session.commit()
            return res.rowcount > 0
