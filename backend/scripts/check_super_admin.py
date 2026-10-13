#!/usr/bin/env python3
"""Check super admin user"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import UserFilter
from app.repositories.user_repository import user_repository


async def check_super_admin():
    admin = await user_repository.findOne(UserFilter(role="super_admin"))
    if admin:
        print("=" * 60)
        print("Super Admin Found:")
        print("=" * 60)
        print(f"Email: {admin.email}")
        print(f"Name: {admin.name}")
        print(f"ID: {admin.id}")
        print("=" * 60)
    else:
        print("No Super Admin found")


if __name__ == "__main__":
    asyncio.run(check_super_admin())
