from typing import Dict

from app.db.storage_factory import get_storage


class ReferralRepository:
    """Referral bonus settings repository."""

    def __init__(self):
        self.storage = get_storage("referralSettings")

    async def get_settings(self) -> Dict:
        settings = await self.storage.findAll()
        if not settings:
            # Initialize with default values as per requirements:
            # - User types: Retail/Business customers
            # - Default: inactive, discount % and percentage value as 0
            default_settings = {
                "_id": "1",
                "retail": {"segment": "retail", "discountType": "percentage", "discountValue": 0, "isActive": False},
                "business": {
                    "segment": "business",
                    "discountType": "percentage",
                    "discountValue": 0,
                    "isActive": False,
                },
            }
            # Note: storage.create will add its own _id if we don't pass one,
            # but FileStorage helper _get_next_id will handle it if we pass one.
            # Actually FileStorage.create adds '_id' automatically.
            await self.storage.create(default_settings)
            return await self.storage.findOne({"_id": "1"}) or default_settings

        doc = dict(settings[0])
        if "retail" not in doc:
            doc["retail"] = {"segment": "retail", "discountType": "percentage", "discountValue": 0, "isActive": False}
        if "business" not in doc:
            doc["business"] = {
                "segment": "business",
                "discountType": "percentage",
                "discountValue": 0,
                "isActive": False,
            }
        return doc

    async def update_settings(self, update_data: Any) -> Dict:
        settings = await self.get_settings()
        return await self.storage.update(settings["_id"], update_data)


referral_repository = ReferralRepository()
