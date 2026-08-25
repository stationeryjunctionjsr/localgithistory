#!/usr/bin/env python3
"""Reset super admin password using passlib format"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository
from app.utils.auth import get_password_hash


async def reset_super_admin_password():
    import os

    email = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_ADMIN_EMAIL", "stationeryjunction.jsr@gmail.com")
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TEST_ADMIN_PASSWORD")
    if not password:
        import secrets

        password = secrets.token_urlsafe(12)
        print(f"[*] TEST_ADMIN_PASSWORD not set. Generated secure random password: {password}")

    try:
        # Find super admin
        admin = await user_repository.findOne({"role": "super_admin"})

        if not admin:
            print("=" * 60)
            print("Super Admin Not Found")
            print("=" * 60)
            print("Please create a super admin first.")
            sys.exit(1)

        print("=" * 60)
        print("Resetting Super Admin Password")
        print("=" * 60)
        print(f"Current Email: {admin.get('email')}")
        print(f"New Password: {password}")

        # Hash password using passlib (same as used in verification)
        hashed_password = get_password_hash(password)

        # Update password
        await user_repository.update(admin["_id"], {"password": hashed_password, "email": email.lower()})

        print("\n[OK] Super Admin Password Reset Successfully!")
        print("=" * 60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(reset_super_admin_password())
