"""
Migration: Alter SJ_GOOGLE_REVIEWS.LAST_UPDATED from VARCHAR2 to TIMESTAMP(6)

The column was VARCHAR2(64) so Oracle returned Oracle-formatted date strings like
'04-JUN-26' instead of ISO 8601. The typed_doc_dao.py _row_to_dict() method calls
.isoformat() on datetime objects but leaves strings as-is, so the VARCHAR2 column
was returned as a non-parseable Oracle date string.

Fix: Convert the column to TIMESTAMP(6), which is consistent with all other date
columns in the database.
"""

import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory


async def main():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: No database connection factory available.")
        return

    async with factory() as session:
        print("Step 1: Check current values in LAST_UPDATED...")
        r = await session.execute(text("SELECT id, last_updated FROM sj_google_reviews"))
        rows = r.fetchall()
        print(f"  Found {len(rows)} row(s):")
        for row in rows:
            print(f"    id={row[0]}  last_updated='{row[1]}'")

        print("\nStep 2: Add a temp TIMESTAMP column...")
        await session.execute(text("ALTER TABLE sj_google_reviews ADD last_updated_ts TIMESTAMP(6)"))
        await session.commit()
        print("  Added last_updated_ts TIMESTAMP(6)")

        print("\nStep 3: Copy parsed values to the temp column...")
        # Oracle TO_TIMESTAMP handles common ISO8601 format
        await session.execute(
            text("""
            UPDATE sj_google_reviews
            SET last_updated_ts = TO_TIMESTAMP(last_updated, 'YYYY-MM-DD"T"HH24:MI:SS.FF6')
            WHERE last_updated IS NOT NULL
              AND REGEXP_LIKE(last_updated, '^[0-9]{4}-[0-9]{2}-[0-9]{2}T')
        """)
        )
        await session.commit()
        print("  Copied ISO8601 values.")

        # Fallback: rows that couldn't be parsed (like '04-JUN-26') — use UPDATED_AT
        await session.execute(
            text("""
            UPDATE sj_google_reviews
            SET last_updated_ts = updated_at
            WHERE last_updated_ts IS NULL
              AND last_updated IS NOT NULL
        """)
        )
        await session.commit()
        print("  Fallback: used updated_at for non-ISO rows.")

        print("\nStep 4: Drop old VARCHAR2 column and rename temp column...")
        await session.execute(text("ALTER TABLE sj_google_reviews DROP COLUMN last_updated"))
        await session.commit()
        print("  Dropped old last_updated VARCHAR2 column.")

        await session.execute(text("ALTER TABLE sj_google_reviews RENAME COLUMN last_updated_ts TO last_updated"))
        await session.commit()
        print("  Renamed last_updated_ts -> last_updated")

        print("\nStep 5: Verify final schema...")
        r = await session.execute(
            text(
                "SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'SJ_GOOGLE_REVIEWS' ORDER BY column_id"
            )
        )
        cols = r.fetchall()
        for c in cols:
            print(f"  {c[0]:25} {c[1]}")

        print("\nStep 6: Verify final data...")
        r = await session.execute(text("SELECT id, last_updated FROM sj_google_reviews"))
        rows = r.fetchall()
        for row in rows:
            print(f"  id={row[0]}  last_updated={row[1]}")

    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(main())
