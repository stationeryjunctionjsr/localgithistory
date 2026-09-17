#!/usr/bin/env python3
"""Update or create super admin user"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository


async def update_or_create_super_admin():
    import os

    email = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_ADMIN_EMAIL", "stationeryjunction.jsr@gmail.com")
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TEST_ADMIN_PASSWORD")
    if not password:
        import secrets

        password = secrets.token_urlsafe(12)
        print(f"[*] TEST_ADMIN_PASSWORD not set. Generated secure random password: {password}")
    name = sys.argv[3] if len(sys.argv) > 3 else os.getenv("TEST_ADMIN_NAME", "Super Admin")

    try:
        # Check if super admin already exists
        existing = await user_repository.findOne({"role": "super_admin"})

        if existing:
            print("=" * 60)
            print("Updating Existing Super Admin")
            print("=" * 60)
            print(f"Current Email: {existing.get('email')}")
            print(f"Updating to Email: {email}")

            # Update the existing super admin
            update_data = {
                "email": email,
                "name": name,
                "password": password,  # Will be hashed by repository
                "isActive": True,
                "approvalStatus": "approved",
            }

            await user_repository.update(existing["_id"], update_data)

            print("\n✓ Super Admin Updated Successfully!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Name: {name}")
            print("=" * 60)
        else:
            # Create new super admin
            print("=" * 60)
            print("Creating New Super Admin")
            print("=" * 60)

            user_data = UserCreate(
                name=name,
                email=email,
                password=password,
                role="super_admin",
                isActive=True,
                approvalStatus="approved",
            )

            user = await user_repository.create(user_data)

            print("\n✓ Super Admin Created Successfully!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Name: {name}")
            print("=" * 60)

        print("\n⚠ IMPORTANT:")
        print("- Change the password after first login")
        print("- Keep these credentials secure")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(update_or_create_super_admin())
