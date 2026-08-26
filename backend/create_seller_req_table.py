import asyncio
import os
import sys

from app.config.database import get_async_session_factory
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def create_table():
    factory = get_async_session_factory()
    if not factory:
        return
    async with factory() as session:
        await session.execute(
            text("""
        CREATE TABLE IF NOT EXISTS sj_seller_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            external_id VARCHAR(255) NOT NULL,
            doc JSON,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE KEY (external_id)
        );
        """)
        )
        await session.commit()
    print("Table sj_seller_requests created or already exists.")


asyncio.run(create_table())
