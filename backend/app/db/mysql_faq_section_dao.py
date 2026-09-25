from typing import Dict
from app.models.faq_section import FaqSection, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.mysql_flat_base_dao import MySQLFlatBaseDAO


class MySQLFaqSectionDAO(MySQLFlatBaseDAO):
    """
    MySQL DAO for sj_faq_sections.
    Handles the child table sj_faq_items for the 'items' API key.
    """

    def __init__(self):
        super().__init__(
            table_name="sj_faq_sections",
            scalar_map={"title": "title", "order_index": "order_index", "is_active": "is_active", "icon": "icon"},
            
            bool_api_keys=frozenset({"is_active"}),
        )

    async def _fetch_items(self, section_id: str) -> List[Dict]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT question, answer FROM sj_faq_items WHERE section_id = :sid ORDER BY id ASC"),
                {"sid": section_id},
            )
            rows = result.fetchall()
            return [{"question": r.question, "answer": r.answer} for r in rows]

    async def _save_items(self, section_id: str, items: List[Dict]):
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

    async def findById(self, id: str) -> Optional[Dict]:
        doc = await super().findById(id)
        if doc:
            doc["items"] = await self._fetch_items(doc["external_id"])
        return doc

    async def findAll(self) -> List[Dict]:
        docs = await super().findAll()
        for doc in docs:
            doc["items"] = await self._fetch_items(doc["external_id"])
        return docs

    async def create(self, data: Dict) -> Dict:
        items = data.pop("items", [])
        created = await super().create(data)
        if created and "externalId" in created:
            await self._save_items(created["external_id"], items)
            created["items"] = await self._fetch_items(created["external_id"])
        return created

    async def update(self, id: str, update_data: Dict) -> Dict:
        items = None
        if "items" in data:
            items = data.pop("items")

        updated = await super().update(id, data)
        # Note: update id is actually externalId
        if updated and items is not None:
            await self._save_items(id, items)
            updated["items"] = await self._fetch_items(id)
        elif updated:
            updated["items"] = await self._fetch_items(id)
        return updated
