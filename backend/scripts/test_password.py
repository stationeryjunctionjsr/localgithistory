#!/usr/bin/env python3
"""Test password verification"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository
from app.utils.auth import verify_password


async def test_password():
    admin = await user_repository.findOne({"role": "super_admin"})
    if admin:
        import os

        password = os.getenv("TEST_ADMIN_PASSWORD", "")
        if not password:
            print("[-] TEST_ADMIN_PASSWORD not set in environment. Using empty password.")
        hash = admin.get("password", "")
        result = verify_password(password, hash)
        print("=" * 60)
        print("Password Verification Test")
        print("=" * 60)
        print(f"Email: {admin.get('email')}")
        print(f"Password: {password}")
        print(f"Verification Result: {result}")
        print("=" * 60)
    else:
        print("Super admin not found")


if __name__ == "__main__":
    asyncio.run(test_password())
