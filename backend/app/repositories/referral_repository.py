from typing import Optional

from app.db.storage_factory import get_storage
from app.models.referral_settings import ReferralSegment, ReferralSettings


class ReferralRepository:
    """Referral bonus settings repository."""

    def __init__(self) -> None:
        self.storage = get_storage("referralSettings")

    async def get_settings(self) -> ReferralSettings:
        settings = await self.storage.findAll()
        if not settings:
            default_settings = ReferralSettings(
                id="1",
                retail=ReferralSegment(segment="retail", discount_type="percentage", discount_value=0.0, is_active=False),
                business=ReferralSegment(segment="business", discount_type="percentage", discount_value=0.0, is_active=False),
            )
            created = await self.storage.create(default_settings)
            return created or default_settings

        setting = settings[0]
        if not setting.retail:
            setting.retail = ReferralSegment(segment="retail", discount_type="percentage", discount_value=0.0, is_active=False)
        if not setting.business:
            setting.business = ReferralSegment(segment="business", discount_type="percentage", discount_value=0.0, is_active=False)
        return setting

    async def update_settings(self, update_data: ReferralSettings) -> Optional[ReferralSettings]:
        settings = await self.get_settings()
        return await self.storage.update(settings.id, update_data)


referral_repository = ReferralRepository()
