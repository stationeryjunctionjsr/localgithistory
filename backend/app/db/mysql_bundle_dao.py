import secrets
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.daos import BundleInternalCreate, BundleItemInternal, BundleInternalUpdate
from app.models.schemas import BundleResponse, BundleItemResponse

class MySQLBundleDAO:
    TABLE = "sj_bundles"

    async def _fetch_products(self, bundle_id: str) -> List[BundleItemResponse]:
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text("SELECT product_id, quantity FROM sj_bundle_products WHERE bundle_id = :b_id"), {"b_id": bundle_id}
            )
            return [BundleItemResponse(productId=row[0], quantity=row[1]) for row in result.all()]

    async def _save_products(self, bundle_id: str, products: List[BundleItemInternal]):
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

    async def _map_row(self, row) -> BundleResponse:
        return BundleResponse(
            _id=str(row.id),
            external_id=row.external_id,
            name=row.name,
            description=row.description,
            price=float(row.price) if row.price is not None else 0.0,
            discount_percentage=float(row.discount_percentage) if row.discount_percentage is not None else None,
            is_active=bool(row.is_active),
            sales_count=row.sales_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
            items=await self._fetch_products(row.external_id)
        )

    async def findById(self, id: str) -> Optional[BundleResponse]:
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        async with SessionLocal() as session:
            res = await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            row = res.fetchone()
            if not row:
                return None
            return await self._map_row(row)

    async def findAll(self) -> List[BundleResponse]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            res = await session.execute(text(f"SELECT * FROM {self.TABLE}"))
            return [await self._map_row(row) for row in res.fetchall()]

    async def create(self, data: BundleInternalCreate) -> BundleResponse:
        SessionLocal = get_async_session_factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        async with SessionLocal() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} (external_id, created_at, updated_at, name, description, price, discount_percentage, is_active, sales_count) VALUES (:eid, :c, :u, :name, :desc, :price, :dp, :ia, :sc)"),
                {
                    "eid": ext_id, "c": now, "u": now,
                    "name": data.name,
                    "desc": data.description,
                    "price": data.price,
                    "dp": data.discount_percentage,
                    "ia": 1 if data.is_active else 0,
                    "sc": data.sales_count or 0
                }
            )
            res = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})
            new_id = res.scalar()
            await session.commit()
            
        items = data.items if data.items else (data.products if data.products else [])
        await self._save_products(ext_id, items)
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: BundleInternalUpdate) -> Optional[BundleResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        now = now_utc()
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        if update_data.name is not None:
            updates.append("name = :name")
            params["name"] = update_data.name
            
        if update_data.description is not None:
            updates.append("description = :desc")
            params["desc"] = update_data.description
            
        if update_data.price is not None:
            updates.append("price = :price")
            params["price"] = update_data.price
            
        if update_data.discount_percentage is not None:
            updates.append("discount_percentage = :dp")
            params["dp"] = update_data.discount_percentage
            
        if update_data.is_active is not None:
            updates.append("is_active = :ia")
            params["ia"] = 1 if update_data.is_active else 0
            
        if update_data.sales_count is not None:
            updates.append("sales_count = :sc")
            params["sc"] = update_data.sales_count
            
        async with SessionLocal() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {','.join(updates)} WHERE id = :id"),
                params
            )
            await session.commit()
            
        items = update_data.items if update_data.items else update_data.products
        if items is not None:
            await self._save_products(existing.external_id, items)
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        SessionLocal = get_async_session_factory()
        pid = int(id) if str(id).isdigit() else None
        async with SessionLocal() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            await session.commit()
            return res.rowcount > 0
