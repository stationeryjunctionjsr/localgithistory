import asyncio
from app.db.storage_factory import get_storage
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def test_db():
    factory = get_async_session_factory()
    async with factory() as session:
        rows = (await session.execute(text("SELECT email, is_on_duty FROM sj_users WHERE role='valet' ORDER BY id DESC LIMIT 5"))).fetchall()
        for r in rows:
            print(f"email: {r.email}, is_on_duty: {r.is_on_duty}")

asyncio.run(test_db())
