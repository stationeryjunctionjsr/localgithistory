from datetime import datetime, timezone
from typing import Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import ReturnSettingsInternal, ReturnSettingsInternalCreate, ReturnSettingsInternalUpdate

class ReturnSettingsRepository:
    def __init__(self):
        self.storage = get_storage("returnSettings")

    async def get_settings(self) -> ReturnSettingsInternal:
        settings = await self.storage.findAll()
        if not settings:
            # Create default settings if they don't exist
            default_settings = ReturnSettingsInternalCreate(
                returnDays=7,
            )
            created = await self.storage.create(default_settings)
            return created
        return settings[0]

    async def update_settings(self, update_data: ReturnSettingsInternalUpdate) -> ReturnSettingsInternal:
        settings = await self.get_settings()
        return await self.storage.update(settings.id, update_data)


return_settings_repository = ReturnSettingsRepository()
