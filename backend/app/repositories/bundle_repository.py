from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.daos import BundleInternalCreate, BundleInternalUpdate
from app.models.schemas import BundleResponse


class BundleRepository:
    """
    Repository for admin-managed product bundles.
    Bundles group multiple products under a single bundle price.
    Stock is tracked per individual product; pricing is bundle-level.
    """

    def __init__(self) -> None:
        self._storage = None
        self._initialized = False

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage("bundles")
        return self._storage

    async def ensure_table_exists(self) -> None:
        if self._initialized:
            return
        self._initialized = True

    async def findAll(self) -> List[BundleResponse]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[BundleResponse]:
        return await self.storage.findById(id)

    async def findOne(self, id: Optional[str] = None) -> Optional[BundleResponse]:
        return await self.storage.findOne(id=id)

    async def create(self, data: BundleInternalCreate) -> BundleResponse:
        await self.ensure_table_exists()
        return await self.storage.create(data)

    async def update(self, id: str, update_data: BundleInternalUpdate) -> Optional[BundleResponse]:
        await self.ensure_table_exists()
        update_data.updated_at = datetime.now(timezone.utc).isoformat()
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        await self.ensure_table_exists()
        return await self.storage.delete(id)

    async def get_active_bundles(self) -> List[BundleResponse]:
        """Return only active (published) bundles."""
        all_bundles = await self.findAll()
        return [b for b in all_bundles if (b.is_active if b.is_active is not None else True)]

    async def get_bundles_containing_product(self, product_id: str) -> List[BundleResponse]:
        """Return all active bundles that include a given product_id."""
        all_bundles = await self.get_active_bundles()
        result = []
        for bundle in all_bundles:
            items = (bundle.items if bundle.items is not None else [])
            if any(i.product_id == product_id for i in items):
                result.append(bundle)
        return result


bundle_repository = BundleRepository()
