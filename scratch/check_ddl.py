import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.database import get_async_session_factory
from sqlalchemy import text


async def main():
    factory = get_async_session_factory()
    if not factory:
        print("DATABASE_URL not set")
        return

    async with factory() as session:
        try:
            # We need to set some DBMS_METADATA transform parameters so the DDL is cleaner
            await session.execute(
                text("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', true); END;")
            )
            await session.execute(
                text(
                    "BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', true); END;"
                )
            )
            await session.execute(
                text(
                    "BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', false); END;"
                )
            )

            result = await session.execute(text("SELECT DBMS_METADATA.GET_DDL('TABLE', 'SJ_USERS') FROM DUAL"))
            ddl = result.scalar()
            print("DDL FOR SJ_USERS:")
            print(ddl)
        except Exception as e:
            print(f"Error fetching DDL: {e}")


if __name__ == "__main__":
    asyncio.run(main())
