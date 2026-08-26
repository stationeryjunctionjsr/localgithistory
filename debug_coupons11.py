
import asyncio
from app.config.settings import settings
print("DB URL:", settings.database_url)
print("Table suffix:", getattr(settings, "table_suffix", ""))

