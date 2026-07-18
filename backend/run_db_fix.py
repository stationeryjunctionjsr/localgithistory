"""
DB Fix Script v2:
1. Delete orphan sessions/carts/wishlists for non-admin users
2. Remove all users except user with email 'stationeryjunction.jsr@gmail.com'
3. Add primary key on USER_ID in sj_users table
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory


async def run():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set")
        return

    async with factory() as session:
        # ── 1. Find admin user ──
        print("=" * 60)
        print("STEP 1: Find admin user")
        print("=" * 60)
        r = await session.execute(
            text("SELECT user_id, email, name, role FROM sj_users WHERE LOWER(email) = :email"),
            {"email": "stationeryjunction.jsr@gmail.com"},
        )
        admin = r.fetchone()

        if not admin:
            print("  ERROR: Admin user NOT FOUND! Aborting.")
            return

        admin_id = admin[0]
        print(f"  Admin: user_id={admin_id}, email={admin[1]}, name={admin[2]}, role={admin[3]}\n")

        # ── 2. Find all FK constraints referencing SJ_USERS ──
        print("=" * 60)
        print("STEP 2: Find FK constraints referencing SJ_USERS")
        print("=" * 60)
        r = await session.execute(
            text("""
            SELECT a.constraint_name, a.table_name, a.r_constraint_name
            FROM user_constraints a
            WHERE a.r_constraint_name IN (
                SELECT constraint_name FROM user_constraints 
                WHERE table_name = 'SJ_USERS' AND constraint_type IN ('P', 'U')
            ) AND a.constraint_type = 'R'
        """)
        )
        fk_constraints = r.fetchall()

        if not fk_constraints:
            # Also check by looking at constraints with table_name containing 'SJ'
            r = await session.execute(
                text("""
                SELECT constraint_name, table_name, r_constraint_name
                FROM user_constraints
                WHERE constraint_type = 'R' 
                AND constraint_name LIKE '%USER%'
            """)
            )
            fk_constraints = r.fetchall()

        for c in fk_constraints:
            print(f"  FK: {c[0]} on table {c[1]}")
        if not fk_constraints:
            print("  No FK constraints found referencing SJ_USERS.")
        print()

        # ── 3. Delete child records from all related tables ──
        print("=" * 60)
        print("STEP 3: Delete child records for non-admin users")
        print("=" * 60)

        # Get list of tables that have user_id FK
        child_tables = set()
        for c in fk_constraints:
            child_tables.add(c[1])

        # Also try common tables that might reference user_id
        possible_children = [
            "SJ_SESSIONS",
            "SJ_CARTS",
            "SJ_WISHLISTS",
            "SJ_ORDERS",
            "SJ_PAYMENTS",
            "SJ_ACTIVITIES",
            "SJ_NOTIFICATIONS",
            "SJ_TRACKING",
            "SJ_SAVED_FOR_LATER",
        ]

        for table in possible_children:
            try:
                # Check if table has USER_ID column
                r = await session.execute(
                    text(
                        f"SELECT column_name FROM user_tab_columns WHERE table_name = :tname AND column_name = 'USER_ID'"
                    ),
                    {"tname": table},
                )
                if r.fetchone():
                    child_tables.add(table)
            except:
                pass

        for table in child_tables:
            try:
                print(f"  Deleting from {table} where user_id != {admin_id}...")
                r = await session.execute(
                    text(f"DELETE FROM {table} WHERE user_id != :admin_id"), {"admin_id": admin_id}
                )
                deleted = r.rowcount
                print(f"    Deleted {deleted} rows.")
            except Exception as e:
                print(f"    Skipped ({e})")

        try:
            await session.commit()
            print("  Committed child deletions.\n")
        except Exception as e:
            print(f"  Commit failed: {e}")
            await session.rollback()
            return

        # ── 4. Delete all non-admin users ──
        print("=" * 60)
        print("STEP 4: Delete all non-admin users")
        print("=" * 60)
        try:
            r = await session.execute(text("DELETE FROM sj_users WHERE user_id != :admin_id"), {"admin_id": admin_id})
            deleted = r.rowcount
            await session.commit()
            print(f"  Deleted {deleted} users.\n")
        except Exception as e:
            print(f"  ERROR: {e}")
            await session.rollback()

            # Try to find the specific blocking tables
            print("  Attempting to find blocking tables...")
            r = await session.execute(
                text("""
                SELECT table_name, constraint_name 
                FROM user_constraints 
                WHERE r_constraint_name IN (
                    SELECT constraint_name FROM user_constraints 
                    WHERE table_name = 'SJ_USERS'
                )
            """)
            )
            blocking = r.fetchall()
            for b in blocking:
                print(f"  Blocking: {b[0]} via {b[1]}")
                try:
                    r2 = await session.execute(
                        text(f"DELETE FROM {b[0]} WHERE user_id != :admin_id"), {"admin_id": admin_id}
                    )
                    print(f"    Deleted {r2.rowcount} rows from {b[0]}")
                except Exception as e2:
                    # Try without user_id filter - maybe column name is different
                    print(f"    Error: {e2}")

            try:
                await session.commit()
                # Retry user deletion
                r = await session.execute(
                    text("DELETE FROM sj_users WHERE user_id != :admin_id"), {"admin_id": admin_id}
                )
                deleted = r.rowcount
                await session.commit()
                print(f"  Retry: Deleted {deleted} users.\n")
            except Exception as e:
                print(f"  Retry failed: {e}")
                await session.rollback()
                return

        # ── 5. Check existing PK ──
        print("=" * 60)
        print("STEP 5: Check and add PRIMARY KEY")
        print("=" * 60)
        r = await session.execute(
            text("SELECT constraint_name, constraint_type FROM user_constraints WHERE table_name = 'SJ_USERS'")
        )
        constraints = r.fetchall()
        has_pk = False
        for c in constraints:
            print(f"  {c[0]} type={c[1]}")
            if c[1] == "P":
                has_pk = True

        if has_pk:
            print("  Primary key already exists.\n")
        else:
            # Ensure NOT NULL
            try:
                await session.execute(text("ALTER TABLE sj_users MODIFY (USER_ID NOT NULL)"))
                await session.commit()
                print("  USER_ID set to NOT NULL.")
            except Exception as e:
                await session.rollback()
                print(f"  USER_ID NOT NULL: {e}")

            # Add PK
            try:
                await session.execute(text("ALTER TABLE sj_users ADD CONSTRAINT PK_SJ_USERS PRIMARY KEY (USER_ID)"))
                await session.commit()
                print("  PRIMARY KEY added!\n")
            except Exception as e:
                await session.rollback()
                print(f"  PK error: {e}\n")

        # ── 6. Final check ──
        print("=" * 60)
        print("STEP 6: Final verification")
        print("=" * 60)
        r = await session.execute(text("SELECT user_id, email, name, role FROM sj_users ORDER BY user_id"))
        users = r.fetchall()
        for u in users:
            print(f"  user_id={u[0]}, email={u[1]}, name={u[2]}, role={u[3]}")
        print(f"  Total users: {len(users)}")

        r = await session.execute(
            text(
                "SELECT constraint_name, constraint_type FROM user_constraints WHERE table_name = 'SJ_USERS' AND constraint_type = 'P'"
            )
        )
        pk = r.fetchone()
        if pk:
            print(f"  PRIMARY KEY: {pk[0]} ✓")
        else:
            print("  WARNING: No primary key found!")

        print("\nDONE!")


if __name__ == "__main__":
    asyncio.run(run())
