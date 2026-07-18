import asyncio
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory


async def apply_schema():
    schema_path = backend_root / "scripts" / "schema_oracle_relational_json.sql"
    if not schema_path.exists():
        print(f"Error: {schema_path} not found.")
        return

    print(f"Reading {schema_path}...")
    content = schema_path.read_text(encoding="utf-8")

    # Simple split by semicolon. For more complex SQL, this might need refinement.
    # Note: Regex to split by semicolon at the end of a line, ignoring internal semicolons.
    statements = re.split(r";\s*$", content, flags=re.MULTILINE)

    factory = get_async_session_factory()
    if not factory:
        print("No factory created. Check DATABASE_URL in .env.")
        return

    async with factory() as session:
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue

            # Filter out comments between statements
            lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
            stmt = "\n".join(lines).strip()
            if not stmt:
                continue

            print(f"Executing: {stmt[:100]}...")
            try:
                # Need a synchronous block or just execute directly
                await session.execute(text(stmt))
                print("  Success.")
            except Exception as e:
                print(f"  Error: {e}")
                # Optional: break or continue

        await session.commit()
    print("Schema application complete.")


if __name__ == "__main__":
    asyncio.run(apply_schema())
