from app.models.daos import BundleInternalCreate, BundleItemInternal, BundleInternalUpdate
from typing import Dict
from app.models.bundle import Bundle, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.mysql_flat_base_dao import MySQLFlatBaseDAO
from app.models.schemas import BundleResponse


class MySQLBundleDAO(MySQLFlatBaseDAO):
    schema_cls = BundleResponse
    def __init__(self):
        super().__init__(
            table_name="sj_bundles",
            scalar_map={
                "name": "name",
                "description": "description",
                "price": "price",
                "discount_percentage": "discount_percentage",
                "is_active": "is_active",
                "sales_count": "sales_count",
            },
            bool_api_keys=frozenset({"is_active"}),
        )

    async def _fetch_products(self, bundle_id: str) -> List[Dict]:
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text("SELECT product_id, quantity FROM sj_bundle_products WHERE bundle_id = :b_id"), {"b_id": bundle_id}
            )
            from app.models.schemas import BundleItemResponse
            return [BundleItemResponse(productId=row[0], quantity=row[1]) for row in result.all()]

    async def _save_products(self, bundle_id: str, products: List["BundleItemInternal"]):
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
                            "p_id": p.product_id,
                            "qty": p.quantity,
                        },
                    )
            await session.commit()

    async def findById(self, id: str) -> Optional[Dict]:
        doc = await super().findById(id)
        if doc:
            doc.items = await self._fetch_products(doc.external_id if doc.external_id is not None else doc.id)
        return doc

    async def findOne(self, query: Dict) -> Optional[Dict]:
        doc = await super().findOne(query)
        if doc:
            doc.items = await self._fetch_products(doc.external_id if doc.external_id is not None else doc.id)
        return doc

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        docs = await super().findAll(query)
        for doc in docs:
            doc.items = await self._fetch_products(doc.external_id if doc.external_id is not None else doc.id)
        return docs

    async def create(self, data: 'BundleInternalCreate, BundleItemInternal') -> Dict:
        data_dict = {}
        try:
            if data.name is not None: data_dict["name"] = data.name
        except AttributeError: pass
        try:
            if data.description is not None: data_dict["description"] = data.description
        except AttributeError: pass
        try:
            if data.price is not None: data_dict["price"] = data.price
        except AttributeError: pass
        try:
            if data.discount_percentage is not None: data_dict["discount_percentage"] = data.discount_percentage
        except AttributeError: pass
        try:
            if data.is_active is not None: data_dict["is_active"] = data.is_active
        except AttributeError: pass
        try:
            if data.sales_count is not None: data_dict["sales_count"] = data.sales_count
        except AttributeError: pass

        items = []
        try:
            if data.items is not None: items = data.items
        except AttributeError: pass
        if not items:
            try:
                if data.products is not None: items = data.products
            except AttributeError: pass
            
        doc = await super().create(data_dict)
        await self._save_products((doc.external_id if doc.external_id is not None else doc.id), items)
        doc.items = await self._fetch_products(doc.external_id if doc.external_id is not None else doc.id)
        return doc

    async def update(self, id: str, update_data: 'BundleInternalUpdate') -> Optional[Dict]:
        update_dict = {}
        try:
            if update_data.name is not None: update_dict["name"] = update_data.name
        except AttributeError: pass
        try:
            if update_data.description is not None: update_dict["description"] = update_data.description
        except AttributeError: pass
        try:
            if update_data.price is not None: update_dict["price"] = update_data.price
        except AttributeError: pass
        try:
            if update_data.discount_percentage is not None: update_dict["discount_percentage"] = update_data.discount_percentage
        except AttributeError: pass
        try:
            if update_data.is_active is not None: update_dict["is_active"] = update_data.is_active
        except AttributeError: pass
        try:
            if update_data.sales_count is not None: update_dict["sales_count"] = update_data.sales_count
        except AttributeError: pass

        items = None
        try:
            if update_data.items is not None: items = update_data.items
        except AttributeError: pass
        if items is None:
            try:
                if update_data.products is not None: items = update_data.products
            except AttributeError: pass

        doc = await super().update(id, update_dict)
        if doc:
            if items is not None:
                await self._save_products((doc.external_id if doc.external_id is not None else doc.id), items)
            doc.items = await self._fetch_products(doc.external_id if doc.external_id is not None else doc.id)
        return doc
