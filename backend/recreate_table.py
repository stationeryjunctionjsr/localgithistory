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
        await session.execute(text("DROP TABLE IF EXISTS sj_seller_requests;"))
        await session.execute(
            text("""
        CREATE TABLE sj_seller_requests (
          id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
          external_id VARCHAR(64) NOT NULL UNIQUE,
          request_number VARCHAR(128) NOT NULL,
          user_id VARCHAR(64),
          subject VARCHAR(255) NOT NULL,
          description TEXT NOT NULL,
          category VARCHAR(64) DEFAULT 'general',
          priority VARCHAR(64) DEFAULT 'medium',
          status VARCHAR(64) DEFAULT 'open',
          attachments JSON,
          responses JSON,
          resolved_at DATETIME,
          closed_at DATETIME,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        )
        await session.commit()
    print("Table sj_seller_requests recreated relationally.")


asyncio.run(create_table())
