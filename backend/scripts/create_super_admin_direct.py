#!/usr/bin/env python3
"""Create super admin user using bcrypt directly"""

import sys
import asyncio
import bcrypt
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository


async def create_super_admin_direct():
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
            print("Super Admin Already Exists")
            print("=" * 60)
            print(f"Email: {existing.get('email')}")
            print(f"Name: {existing.get('name')}")
            print("\nUpdating email to:", email)

            # Update email only
            await user_repository.update(existing["_id"], {"email": email, "name": name})
            print("\n[OK] Super Admin Email Updated!")
            print("=" * 60)
            return

        # Hash password using bcrypt directly
        password_bytes = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        # Get all users to find max userId
        all_users = await user_repository.findAll()
        max_id = 0
        for user in all_users:
            if user.get("userId") and isinstance(user.get("userId"), int):
                max_id = max(max_id, user.get("userId", 0))
        user_id = max_id + 1

        # Create user data
        user_data = {
            "userId": user_id,
            "name": name,
            "email": email.lower(),
            "password": hashed_password,
            "role": "super_admin",
            "phone": "",
            "companyName": "",
            "address": {},
            "isActive": True,
            "approvalStatus": "approved",
            "isDeactivated": False,
            "creditLimit": 0,
            "creditUsed": 0,
            "paymentTerms": "30",
        }

        # Use storage directly to bypass repository validation
        user = await user_repository.storage.create(user_data)

        print("=" * 60)
        print("Super Admin Created Successfully!")
        print("=" * 60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Name: {name}")
        print("\nIMPORTANT:")
        print("- Change the password after first login")
        print("- Only one super admin is allowed in the system")
        print("- Keep these credentials secure")
        print("=" * 60)

    except Exception as e:
        print(f"Error creating super admin: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_super_admin_direct())
