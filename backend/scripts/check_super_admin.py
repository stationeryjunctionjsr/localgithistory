#!/usr/bin/env python3
"""Check super admin user"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository


async def check_super_admin():
    admin = await user_repository.findOne({"role": "super_admin"})
    if admin:
        print("=" * 60)
        print("Super Admin Found:")
        print("=" * 60)
        print(f"Email: {admin.get('email')}")
        print(f"Name: {admin.get('name')}")
        print(f"ID: {admin.get('_id')}")
        print("=" * 60)
    else:
        print("No Super Admin found")


if __name__ == "__main__":
    asyncio.run(check_super_admin())
