from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.mysql_flat_base_dao import MySQLFlatBaseDAO


class MySQLBundleDAO(MySQLFlatBaseDAO):
    def __init__(self):
        super().__init__(
            table_name="sj_bundles",
            scalar_map={
                "name": "name",
                "description": "description",
                "price": "price",
                "discountPercentage": "discount_percentage",
                "isActive": "is_active",
                "salesCount": "sales_count",
            },
            
            bool_api_keys=frozenset({"isActive"}),
        )

    async def _fetch_products(self, bundle_id: str) -> List[Dict]:
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text("SELECT product_id, quantity FROM sj_bundle_products WHERE bundle_id = :b_id"), {"b_id": bundle_id}
            )
            return [{"productId": row[0], "quantity": row[1]} for row in result.all()]

    async def _save_products(self, bundle_id: str, products: List[Dict]):
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(text("DELETE FROM sj_bundle_products WHERE bundle_id = :b_id"), {"b_id": bundle_id})
            if products:
                stmt = text(
                    "INSERT INTO sj_bundle_products (bundle_id, product_id, quantity) VALUES (:b_id, :p_id, :qty)"
                )
                for p in products:
                    await session.execute(
                        stmt,
                        {
                            "b_id": bundle_id,
                            "p_id": p.get("productId") or p.get("product_id"),
                            "qty": p.get("quantity", 1),
                        },
                    )
            await session.commit()

    async def findById(self, id: str) -> Optional[Dict]:
        doc = await super().findById(id)
        if doc:
            doc["items"] = await self._fetch_products(doc.get("external_id"))
        return doc

    async def findOne(self, query: Dict) -> Optional[Dict]:
        doc = await super().findOne(query)
        if doc:
            doc["items"] = await self._fetch_products(doc.get("external_id"))
        return doc

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        docs = await super().findAll(query)
        for doc in docs:
            doc["items"] = await self._fetch_products(doc.get("external_id"))
        return docs

    async def create(self, data: Dict) -> Dict:
        items = data.pop("items", [])
        # Fallback to products if passed
        if not items and "products" in data:
            items = data.pop("products")
        doc = await super().create(data)
        await self._save_products(doc.get("external_id"), items)
        doc["items"] = await self._fetch_products(doc.get("external_id"))
        return doc

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        items = None
        if "items" in update_data:
            items = update_data.pop("items")
        elif "products" in update_data:
            items = update_data.pop("products")

        doc = await super().update(id, update_data)
        if doc:
            if items is not None:
                await self._save_products(doc.get("external_id"), items)
            doc["items"] = await self._fetch_products(doc.get("external_id"))
        return doc
