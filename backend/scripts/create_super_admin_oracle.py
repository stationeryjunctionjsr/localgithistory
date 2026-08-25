import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

load_dotenv()

from app.repositories.user_repository import user_repository


async def create_super_admin():
    email = os.getenv("TEST_ADMIN_EMAIL", "stationeryjunction.jsr@gmail.com")

    password = os.getenv("TEST_ADMIN_PASSWORD")
    if not password:
        import secrets

        password = secrets.token_urlsafe(12)
        print(f"[*] TEST_ADMIN_PASSWORD not set in environment. Generated secure random password: {password}")

    name = os.getenv("TEST_ADMIN_NAME", "Super Admin")

    try:
        # Check if super admin already exists in Oracle
        existing = await user_repository.findOne({"role": "super_admin"})
        if existing:
            print(f"Super Admin Already Exists in Oracle: {existing.get('email')}")
            return

        # Create super admin
        user_data = {
            "name": name,
            "email": email,
            "password": password,
            "role": "super_admin",
            "isActive": True,
            "approvalStatus": "approved",
        }

        user = await user_repository.create(user_data)
        print(f"Super Admin Created Successfully in Oracle: {email}")

    except Exception as e:
        print(f"Error creating super admin: {str(e)}")


if __name__ == "__main__":
    asyncio.run(create_super_admin())
