#!/usr/bin/env python3
"""Fix super admin password - verify and update if needed"""

import sys
import asyncio
import bcrypt
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository


async def fix_super_admin_password():
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
            sys.exit(1)

        print("=" * 60)
        print("Fixing Super Admin Password")
        print("=" * 60)
        print(f"Email: {admin.get('email')}")

        # Check if current password hash works
        current_hash = admin.get("password", "")
        if current_hash:
            # Try to verify with bcrypt directly
            try:
                password_bytes = password.encode("utf-8")
                hash_bytes = current_hash.encode("utf-8")
                if bcrypt.checkpw(password_bytes, hash_bytes):
                    print("Current password hash is valid!")
                    # Just update email if needed
                    if admin.get("email") != email.lower():
                        await user_repository.update(admin["_id"], {"email": email.lower()})
                        print(f"Email updated to: {email}")
                    print("=" * 60)
                    return
            except Exception as e:
                print(f"Current hash verification failed: {e}")
                print("Will create new hash...")

        # Create new hash using bcrypt (compatible format)
        password_bytes = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        # Update password and email
        await user_repository.update(admin["_id"], {"password": hashed_password, "email": email.lower()})

        print("\n[OK] Super Admin Password Updated!")
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
    asyncio.run(fix_super_admin_password())
