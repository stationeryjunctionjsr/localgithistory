import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import asyncio
from unittest.mock import patch

# Mock use_oracle to return False for this test
with patch("app.config.database.use_oracle", return_value=False):
    from app.main import initialize_data_dir
    from app.config.settings import settings

    print("Original environment:", settings.environment)

    async def test_startup():
        for env in ["development", "uat", "production"]:
            print(f"\n--- Testing startup directories for environment: {env} ---")
            settings.environment = env
            await initialize_data_dir()

            # Verify folders exist
            base_dir = Path(__file__).resolve().parents[1] / "uploads"
            env_folder = "SJ_PROD" if env == "production" else ("SJ_UAT" if env == "uat" else "SJ_LOCAL")

            subfolders = ["categories", "products", "brands", "invoices"]
            for subfolder in subfolders:
                path = base_dir / env_folder / subfolder
                if path.exists():
                    print(f"Verified directory exists: {path}")
                else:
                    print(f"Error! Directory does not exist: {path}")

    if __name__ == "__main__":
        asyncio.run(test_startup())
        print("\nStartup verification completed successfully!")
