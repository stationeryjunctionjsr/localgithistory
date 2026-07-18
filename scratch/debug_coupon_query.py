import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory, get_async_engine

async def main():
    print("[*] Direct select test...")
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            print("Executing direct select on user_tables...")
            res = await asyncio.wait_for(session.execute(text("SELECT table_name FROM user_tables WHERE table_name = 'SJ_COUPONS_UAT'")), timeout=5)
            print(f"Table exists: {res.fetchone()}")
            
            print("Executing direct count on sj_coupons_uat...")
            res2 = await asyncio.wait_for(session.execute(text("SELECT COUNT(*) FROM sj_coupons_uat")), timeout=5)
            print(f"Count: {res2.scalar()}")
        except asyncio.TimeoutError:
            print("TIMEOUT: Select timed out, table might be locked!")
        except Exception as e:
            print(f"Error: {e}")
            
    engine = get_async_engine()
    if engine:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
