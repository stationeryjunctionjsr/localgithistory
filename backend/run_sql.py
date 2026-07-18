import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

async def main():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    engine = create_async_engine(db_url, echo=True)
        
    async with engine.begin() as conn:
        with open("scripts/add_indices.sql", "r") as f:
            sql = f.read()
        
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement and not statement.startswith("--"):
                try:
                    await conn.execute(text(statement))
                    print(f"Successfully executed: {statement[:50]}...")
                except Exception as e:
                    print(f"Error executing {statement[:50]}... : {e}")

if __name__ == "__main__":
    asyncio.run(main())
