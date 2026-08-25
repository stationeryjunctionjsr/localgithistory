import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.database import get_async_engine, get_async_session_factory
from app.config.settings import settings
from app.db.storage_factory import get_storage
from sqlalchemy import text


async def main():
    print("[*] Starting SavedForLater UAT Database Verification...")

    settings.table_suffix = "_UAT"
    store = get_storage("savedForLater")

    # Clean up leftover
    await store.delete("TEST_USER_999")

    data = {"user": "TEST_USER_999", "items": [{"productId": "1001"}, {"productId": "1002"}]}

    try:
        new_doc = await store.create(data)
        print(f"  [+] Created saved-for-later record for user: {new_doc['user']}")

        # Query database directly to check columns in sj_saved_for_later_uat
        factory = get_async_session_factory()
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT user_id, product_id FROM sj_saved_for_later_uat WHERE user_id = 'TEST_USER_999' ORDER BY product_id"
                )
            )
            rows = result.fetchall()
            assert len(rows) == 2, f"Expected 2 rows in sj_saved_for_later_uat table, got {len(rows)}!"
            print(f"  [+] DB Direct Rows: {[(r[0], r[1]) for r in rows]}")
            assert rows[0][0] == "TEST_USER_999", "user_id mismatch"
            assert rows[0][1] == "1001", "product_id mismatch"
            assert rows[1][1] == "1002", "product_id mismatch"

        # Clean up
        await store.delete("TEST_USER_999")
        print("[+] SavedForLater UAT verification completed successfully!")
    except Exception as e:
        print(f"  [-] Verification failed: {e}")
    finally:
        engine = get_async_engine()
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
