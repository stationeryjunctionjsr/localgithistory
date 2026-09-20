import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory
from dotenv import load_dotenv

load_dotenv('.env')

async def main():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(text('''
            ALTER TABLE sj_events 
            DROP COLUMN session_id, 
            DROP COLUMN user_id, 
            DROP COLUMN ip_address, 
            DROP COLUMN os, 
            DROP COLUMN browser, 
            DROP COLUMN campaign, 
            DROP COLUMN source, 
            DROP COLUMN device_type, 
            DROP COLUMN device_os
        '''))
        await session.commit()
        print("Columns dropped from sj_events successfully.")

asyncio.run(main())
