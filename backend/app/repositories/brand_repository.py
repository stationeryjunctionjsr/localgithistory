from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class BrandRepository:
    def __init__(self):
        self.storage = get_storage("brands")

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        items = await self.storage.findAll(query or {})
        if query and query.get("isActive") is not None:
            items = [b for b in items if b.get("isActive") == query["isActive"]]
        return sorted(items, key=lambda x: (x.get("name") or "").lower())

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActive(self) -> List[Dict]:
        items = await self.storage.findAll()
        return sorted(
            [b for b in items if b.get("isActive", True) is True], key=lambda x: (x.get("name") or "").lower()
        )

    async def create(self, data: Dict):
        return await self.storage.create(
            {
                "name": data.get("name", ""),
                "logoUrl": data.get("logoUrl", ""),
                "isActive": data.get("isActive", True) if "isActive" in data else True,
                "showInMobileHomepage": data.get("showInMobileHomepage", False),
            }
        )

    async def update(self, id: str, data: Dict):
        return await self.storage.update(id, data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


brand_repository = BrandRepository()
