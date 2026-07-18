import asyncio
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Set up paths so we can import from backend root
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

# List of independent tables (for priority creation, though retry loop handles it too)
TABLES_TO_CLONE = [
    "SJ_ABOUT_US", "SJ_ACTIVITIES", "SJ_BANNERS", "SJ_BRANDS", "SJ_BUNDLES",
    "SJ_CARTS", "SJ_CATEGORIES", "SJ_CATEGORY_TAGS", "SJ_COACH_MARKS", "SJ_COLLECTIONS",
    "SJ_CONTACTS", "SJ_COUPONS", "SJ_CUSTOMER_SEGMENTS", "SJ_DELIVERY_CHARGES", "SJ_DELIVERY_CHARGE_DEFAULTS",
    "SJ_DEVICE_SUBSCRIPTIONS", "SJ_EMAIL_OTPS", "SJ_EMAIL_OTP_SEND_LOG", "SJ_EVENTS", "SJ_FAQ_SECTIONS",
    "SJ_FEATURE_FLAGS", "SJ_GOOGLE_REVIEWS", "SJ_NOTIFICATIONS", "SJ_ORDERS", "SJ_ORDER_FEEDBACK",
    "SJ_ORDER_ITEMS", "SJ_OTPS", "SJ_OTP_SEND_LOG", "SJ_PAYMENTS", "SJ_PAYMENT_ENTRIES",
    "SJ_PRIVACY_POLICY", "SJ_PRODUCTS", "SJ_PRODUCT_NOTIFICATIONS", "SJ_PRODUCT_REVIEWS", "SJ_PROMO_STRIPS",
    "SJ_PUSH_NOTIFICATIONS", "SJ_REFERRAL_SETTINGS", "SJ_RETURN_REQUESTS", "SJ_RETURN_SETTINGS", "SJ_REVIEW_CLASSIFICATIONS",
    "SJ_SAVED_FOR_LATER", "SJ_SCHEMES", "SJ_SEARCH_TAGS", "SJ_SESSIONS", "SJ_STOCK_RESERVATIONS",
    "SJ_SUPPORT_TICKETS", "SJ_TRACKING", "SJ_USERS", "SJ_WISHLISTS"
]

async def main():
    factory = get_async_session_factory()
    if not factory:
        print("[-] Error: DATABASE_URL not configured.")
        return

    async with factory() as session:
        # Enable clean metadata DDL formatting
        await session.execute(text("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', true); END;"))
        await session.execute(text("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', true); END;"))
        await session.execute(text("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', false); END;"))
        await session.commit()

        # Step 1: Drop existing UAT tables to start fresh
        print("[*] Step 1: Dropping existing _UAT tables (if any)...")
        for table in TABLES_TO_CLONE:
            uat_table = f"{table}_UAT"
            try:
                await session.execute(text(f"DROP TABLE {uat_table} CASCADE CONSTRAINTS"))
                await session.commit()
                print(f"    Dropped {uat_table}")
            except Exception as e:
                # Table might not exist, which is fine
                await session.rollback()

        # Step 2: Fetch, modify, and create UAT tables using a retry loop to satisfy FK constraints
        print("\n[*] Step 2: Fetching and creating UAT tables...")
        table_ddls = {}
        for table in TABLES_TO_CLONE:
            try:
                res = await session.execute(text(f"SELECT DBMS_METADATA.GET_DDL('TABLE', '{table}') FROM DUAL"))
                ddl = res.scalar()
                
                # Transform the DDL for UAT
                # 1. Remove schema prefix e.g. "ADMIN"."SJ_USERS" -> "SJ_USERS"
                ddl = re.sub(r'"[A-Za-z0-9_]+"\."(SJ_[A-Za-z0-9_]+)"', r'"\1"', ddl)
                
                # 2. Rename all SJ_ tables to SJ_..._UAT
                for t in TABLES_TO_CLONE:
                    ddl = re.sub(rf'"{t}"', f'"{t}_UAT"', ddl)
                    ddl = re.sub(rf'\b{t}\b', f'{t}_UAT', ddl)

                # 3. Rename constraint names to append _UAT
                ddl = re.sub(r'CONSTRAINT\s+"([^"]+)"', r'CONSTRAINT "\1_UAT"', ddl)

                # 4. Rename index names inside USING INDEX statements
                ddl = re.sub(r'USING INDEX\s+"([^"]+)"', r'USING INDEX "\1_UAT"', ddl)

                # Remove any SQL terminators at the end so sqlalchemy can execute it safely
                ddl = ddl.strip()
                if ddl.endswith(";"):
                    ddl = ddl[:-1]

                table_ddls[table] = ddl
            except Exception as e:
                print(f"    [-] Failed to get DDL for {table}: {e}")

        # Retry loop to create tables
        pending_tables = list(table_ddls.keys())
        attempts = 0
        max_attempts = 10

        while pending_tables and attempts < max_attempts:
            attempts += 1
            print(f"    Attempt {attempts} to create pending tables (remaining: {len(pending_tables)})...")
            created_in_this_loop = []
            
            for table in pending_tables:
                uat_table = f"{table}_UAT"
                ddl = table_ddls[table]
                try:
                    await session.execute(text(ddl))
                    await session.commit()
                    created_in_this_loop.append(table)
                    print(f"      Created table {uat_table}")
                except Exception as e:
                    await session.rollback()
                    # Print error for debugging in last attempt or if needed
                    # E.g. parent table might not exist yet
                    pass
            
            if not created_in_this_loop:
                print("    [-] Deadlock or syntax error detected. No tables created in this iteration.")
                break
                
            for table in created_in_this_loop:
                pending_tables.remove(table)

        if pending_tables:
            print(f"    [-] Error: Could not create tables: {pending_tables}")
            return
        else:
            print("[+] All UAT tables created successfully!")

        # Step 3: Copy super admin credentials from SJ_USERS to SJ_USERS_UAT
        print("\n[*] Step 3: Copying super admin credentials to SJ_USERS_UAT...")
        try:
            # Check if super admin exists in original table
            res = await session.execute(
                text("SELECT COUNT(*) FROM SJ_USERS WHERE LOWER(email) = 'stationeryjunction.jsr@gmail.com'")
            )
            cnt = res.scalar()
            if cnt > 0:
                await session.execute(
                    text("""
                        INSERT INTO SJ_USERS_UAT 
                        SELECT * FROM SJ_USERS 
                        WHERE LOWER(email) = 'stationeryjunction.jsr@gmail.com'
                    """)
                )
                await session.commit()
                print("[+] Super admin user credentials copied successfully.")
            else:
                print("[-] Warning: Super admin user stationeryjunction.jsr@gmail.com not found in SJ_USERS.")
        except Exception as e:
            await session.rollback()
            print(f"[-] Error copying super admin: {e}")

        # Step 4: Reset identity sequences using START WITH LIMIT VALUE
        print("\n[*] Step 4: Resetting UAT table identity sequences...")
        for table in TABLES_TO_CLONE:
            uat_table = f"{table}_UAT"
            try:
                # Find if table has an identity column
                res = await session.execute(
                    text("SELECT column_name FROM user_tab_identity_cols WHERE table_name = :tname"),
                    {"tname": uat_table}
                )
                row = res.fetchone()
                if row:
                    col_name = row[0]
                    # Reset the sequence start to max(col) + 1 (or 1 if empty)
                    await session.execute(
                        text(f"ALTER TABLE {uat_table} MODIFY ({col_name} GENERATED BY DEFAULT AS IDENTITY (START WITH LIMIT VALUE))")
                    )
                    await session.commit()
                    print(f"    Reset identity sequence on {uat_table}.{col_name}")
            except Exception as e:
                await session.rollback()
                print(f"    [-] Failed to reset identity on {uat_table}: {e}")

        # Step 5: Fetch and clone custom indexes
        print("\n[*] Step 5: Fetching and creating custom indexes...")
        try:
            res = await session.execute(
                text("""
                    SELECT index_name, table_name FROM user_indexes 
                    WHERE table_name LIKE 'SJ_%' AND table_name NOT LIKE '%_UAT' 
                      AND index_name NOT LIKE 'SYS_%' AND index_name NOT LIKE '%_UAT'
                """)
            )
            indexes = res.fetchall()
            print(f"    Found {len(indexes)} user-defined indexes to clone.")
            
            for idx_row in indexes:
                idx_name = idx_row[0]
                tbl_name = idx_row[1]
                uat_idx_name = f"{idx_name}_UAT"
                uat_tbl_name = f"{tbl_name}_UAT"
                
                try:
                    # Drop existing UAT index if any
                    try:
                        await session.execute(text(f"DROP INDEX {uat_idx_name}"))
                        await session.commit()
                    except:
                        await session.rollback()

                    # Get original index DDL
                    idx_res = await session.execute(text(f"SELECT DBMS_METADATA.GET_DDL('INDEX', '{idx_name}') FROM DUAL"))
                    idx_ddl = idx_res.scalar()
                    
                    # Transform the DDL for UAT
                    # 1. Remove schema prefix
                    idx_ddl = re.sub(r'"[A-Za-z0-9_]+"\."([A-Za-z0-9_]+)"', r'"\1"', idx_ddl)
                    # 2. Rename index name
                    idx_ddl = re.sub(rf'"{idx_name}"', f'"{uat_idx_name}"', idx_ddl)
                    idx_ddl = re.sub(rf'\b{idx_name}\b', uat_idx_name, idx_ddl)
                    # 3. Rename table name
                    idx_ddl = re.sub(rf'"{tbl_name}"', f'"{uat_tbl_name}"', idx_ddl)
                    idx_ddl = re.sub(rf'\b{tbl_name}\b', uat_tbl_name, idx_ddl)
                    
                    idx_ddl = idx_ddl.strip()
                    if idx_ddl.endswith(";"):
                        idx_ddl = idx_ddl[:-1]
                        
                    await session.execute(text(idx_ddl))
                    await session.commit()
                    print(f"      Created index {uat_idx_name} on {uat_tbl_name}")
                except Exception as e:
                    await session.rollback()
                    print(f"      [-] Failed to clone index {idx_name}: {e}")
        except Exception as e:
            print(f"[-] Error querying indexes: {e}")

        print("\n[+] Database cloning completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
