from datetime import datetime, timezone
from typing import Dict

from app.db.storage_factory import get_storage


class ReturnSettingsRepository:
    def __init__(self):
        self.storage = get_storage("returnSettings")

    async def get_settings(self) -> Dict:
        settings = await self.storage.findAll()
        if not settings:
            # Create default settings if they don't exist
            default_settings = {
                "returnDays": 7,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
            created = await self.storage.create(default_settings)
            return created
        return settings[0]

    async def update_settings(self, update_data: Dict) -> Dict:
        settings = await self.get_settings()
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return await self.storage.update(settings["_id"], update_data)


return_settings_repository = ReturnSettingsRepository()
