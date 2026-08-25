import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv


async def main():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("oracle:"):
        db_url = "oracle+oracledb:" + db_url[6:]

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        print("Checking max sessions and processes...")
        result = await conn.execute(text("SELECT name, value FROM v$parameter WHERE name IN ('sessions', 'processes')"))
        for row in result:
            print(f"{row.name}: {row.value}")

        print("\nChecking current resource limit usage...")
        result = await conn.execute(
            text(
                "SELECT resource_name, current_utilization, max_utilization, limit_value FROM v$resource_limit WHERE resource_name IN ('processes', 'sessions')"
            )
        )
        for row in result:
            print(
                f"{row.resource_name} - Current: {row.current_utilization}, Max Used: {row.max_utilization}, Limit: {row.limit_value}"
            )


if __name__ == "__main__":
    asyncio.run(main())
