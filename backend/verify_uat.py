import asyncio
from app.config.database import get_async_session_factory
from sqlalchemy import text

async def run():
    factory = get_async_session_factory()
    async with factory() as session:
        res = await session.execute(text("SHOW DATABASES;"))
        print("DATABASES:", [row[0] for row in res.fetchall()])
        
        print("\n--- SCHEMA VERIFICATION (UAT) ---")
        
        # sj_tracking
        try:
            res = await session.execute(text("DESCRIBE sj_tracking;"))
            cols = [row[0] for row in res.fetchall()]
            print("sj_tracking columns:", cols)
            print("  Has os/browser?", "os" in cols or "browser" in cols)
        except Exception as e:
            print("sj_tracking error:", e)

        # sj_analytics_sessions
        try:
            res = await session.execute(text("DESCRIBE sj_analytics_sessions;"))
            cols = [row[0] for row in res.fetchall()]
            print("\nsj_analytics_sessions columns:", cols)
            print("  Has is_returning?", "is_returning" in cols)
            print("  Has auth_session_id?", "auth_session_id" in cols)
            print("  Has device columns (os)?", "os" in cols)
        except Exception as e:
            print("sj_analytics_sessions error:", e)

        # sj_activities
        try:
            res = await session.execute(text("DESCRIBE sj_activities;"))
            print("\nsj_activities exists!")
        except Exception as e:
            print("\nsj_activities does not exist (Good!)")

        # sj_session_devices
        try:
            res = await session.execute(text("DESCRIBE sj_session_devices;"))
            print("\nsj_session_devices exists!")
        except Exception as e:
            print("\nsj_session_devices does not exist (Good!)")
            
        # sj_sessions
        try:
            res = await session.execute(text("DESCRIBE sj_sessions;"))
            cols = [row[0] for row in res.fetchall()]
            print("\nsj_sessions columns:", cols)
            print("  Has device?", "device" in cols)
        except Exception as e:
            print("sj_sessions error:", e)

asyncio.run(run())
