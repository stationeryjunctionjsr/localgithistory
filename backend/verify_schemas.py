import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_db(db_name):
    print(f"\n======================================")
    print(f"VERIFYING DATABASE: {db_name}")
    print(f"======================================")
    try:
        url = f"mysql+aiomysql://stationeryjunction.jsr%40gmail.com:Jaimatadi%241607@127.0.0.1:13306/{db_name}"
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            
            async def get_cols(table):
                try:
                    res = await conn.execute(text(f"DESCRIBE {table};"))
                    return [row[0] for row in res.fetchall()]
                except Exception:
                    return None

            print("\n--- Checking DROPPED Tables ---")
            for t in ["sj_activities", "sj_activity_meta", "sj_session_devices"]:
                cols = await get_cols(t)
                if cols is None:
                    print(f"[PASS] {t} correctly dropped")
                else:
                    print(f"[FAIL] {t} STILL EXISTS!")

            print("\n--- Checking sj_sessions ---")
            cols = await get_cols("sj_sessions")
            if cols:
                if "device" in cols:
                    print("[FAIL] sj_sessions.device column STILL EXISTS!")
                else:
                    print("[PASS] sj_sessions.device column correctly dropped")
            else:
                print("[FAIL] sj_sessions table missing!")

            print("\n--- Checking sj_tracking ---")
            cols = await get_cols("sj_tracking")
            if cols:
                if "page_views" in cols:
                    print("[FAIL] sj_tracking.page_views STILL EXISTS!")
                else:
                    print("[PASS] sj_tracking.page_views correctly dropped")
                
                bad_cols = ["os", "browser", "ip_address", "is_returning", "campaign", "device_type", "device_os_version", "device_model", "device_app_version"]
                found_bad = [c for c in bad_cols if c in cols]
                if found_bad:
                    print(f"[FAIL] sj_tracking redundant device cols STILL EXIST: {found_bad}")
                else:
                    print("[PASS] sj_tracking redundant device columns correctly dropped")
                    
                if "page" in cols:
                    print("[PASS] sj_tracking.page column exists")
                else:
                    print("[FAIL] sj_tracking.page column MISSING!")
            else:
                print("[FAIL] sj_tracking table missing!")

            print("\n--- Checking sj_analytics_sessions ---")
            cols = await get_cols("sj_analytics_sessions")
            if cols:
                if "is_returning" in cols:
                    print("[FAIL] sj_analytics_sessions.is_returning STILL EXISTS!")
                else:
                    print("[PASS] sj_analytics_sessions.is_returning correctly dropped")
                    
                if "auth_session_id" in cols:
                    print("[PASS] sj_analytics_sessions.auth_session_id exists")
                else:
                    print("[FAIL] sj_analytics_sessions.auth_session_id MISSING!")
                    
                required_cols = ["session_id", "user_id", "source", "os", "browser", "device_model", "campaign", "time_spent_seconds"]
                missing = [c for c in required_cols if c not in cols]
                if missing:
                    print(f"[FAIL] sj_analytics_sessions missing required columns: {missing}")
                else:
                    print("[PASS] sj_analytics_sessions has all expected device columns")
            else:
                print("[FAIL] sj_analytics_sessions table MISSING!")

    except Exception as e:
        print(f"Failed to connect or query {db_name}: {e}")

async def run():
    await check_db("sjuatdb")
    await check_db("sjqadb")

asyncio.run(run())
