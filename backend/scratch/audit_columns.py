import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

QUERY = (
    "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE "
    "FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = DATABASE() "
    "AND TABLE_NAME LIKE 'sj_%' "
    "AND COLUMN_TYPE IN ('longtext', 'json', 'text', 'mediumtext') "
    "ORDER BY TABLE_NAME, COLUMN_NAME"
)

async def main():
    f = get_async_session_factory()
    async with f() as s:
        res = await s.execute(text(QUERY))
        rows = res.fetchall()
        for r in rows:
            print(f"{r[0]}.{r[1]} ({r[2]})")

asyncio.run(main())
