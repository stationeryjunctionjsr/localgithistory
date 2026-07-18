#!/usr/bin/env python3
"""Update super admin email only (without changing password)"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository


async def set_super_admin_email():
    email = sys.argv[1] if len(sys.argv) > 1 else "stationeryjunction.jsr@gmail.com"

    try:
        # Check if super admin already exists
        existing = await user_repository.findOne({"role": "super_admin"})

        if existing:
            print("=" * 60)
            print("Updating Super Admin Email")
            print("=" * 60)
            print(f"Current Email: {existing.get('email')}")
            print(f"New Email: {email}")

            # Update only the email (no password change)
            update_data = {"email": email, "name": existing.get("name", "Super Admin")}

            await user_repository.update(existing["_id"], update_data)

            print("\n✓ Super Admin Email Updated Successfully!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Name: {existing.get('name', 'Super Admin')}")
            print("\nNote: Password was not changed.")
            print("=" * 60)
        else:
            print("=" * 60)
            print("No Super Admin Found")
            print("=" * 60)
            print("Please create a super admin first using the create_super_admin.py script")
            print("or use the API to create one.")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(set_super_admin_email())
