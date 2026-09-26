from typing import TYPE_CHECKING, Any
from typing import Dict

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
        from app.models.schemas import ReferralSettings



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

        setting = settings[0]
        from app.models.referral_settings import ReferralSegment
        if not setting.retail:
            setting.retail = ReferralSegment(segment="retail", discount_type="percentage", discount_value=0, is_active=False)
        if not setting.business:
            setting.business = ReferralSegment(segment="business", discount_type="percentage", discount_value=0, is_active=False)
        return setting

    async def update_settings(self, update_data: 'ReferralSettings') -> Dict:
        settings = await self.get_settings()
        return await self.storage.update(settings.id, update_data)


referral_repository = ReferralRepository()
