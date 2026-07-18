#!/usr/bin/env python3
"""Create super admin user"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository


async def create_super_admin():
    email = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_ADMIN_EMAIL", "stationeryjunction.jsr@gmail.com")
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TEST_ADMIN_PASSWORD")
    if not password:
        import secrets
        password = secrets.token_urlsafe(12)
        print(f"[*] TEST_ADMIN_PASSWORD not set in environment or arguments. Generated secure random password: {password}")
    name = sys.argv[3] if len(sys.argv) > 3 else os.getenv("TEST_ADMIN_NAME", "Super Admin")

    try:
        # Check if super admin already exists
        existing = await user_repository.findOne({"role": "super_admin"})
        if existing:
            print("=" * 60)
            print("Super Admin Already Exists")
            print("=" * 60)
            print(f"Email: {existing.get('email')}")
            print(f"Name: {existing.get('name')}")
            print("\nOnly one super admin is allowed in the system.")
            print("If you need to reset the password, delete the existing admin first.")
            print("=" * 60)
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

        print("=" * 60)
        print("Super Admin Created Successfully!")
        print("=" * 60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Name: {name}")
        print("\n⚠ IMPORTANT:")
        print("- Change the password after first login")
        print("- Only one super admin is allowed in the system")
        print("- Keep these credentials secure")
        print("=" * 60)

    except Exception as e:
        print(f"Error creating super admin: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_super_admin())
