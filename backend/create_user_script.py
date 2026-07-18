import asyncio
import sys
import os

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.repositories.user_repository import user_repository
from app.utils.auth import get_password_hash


async def create_admin_user():
    email = "testadmin@stationery.com"

    # Check if user already exists
    existing = await user_repository.findByEmail(email)
    if existing:
        print(f"User {email} already exists.")
        new_hash = get_password_hash("password123")
        await user_repository.update(existing["_id"], {"password": new_hash})
        print("Password reset to 'password123'")
        return

    new_user = {
        "name": "Stationery Admin",
        "email": email,
        "password": get_password_hash("password123"),
        "role": "super_admin",
        "isActive": True,
        "phone": "9876543210",  # Dummy phone
        "approvalStatus": "approved",
    }

    created = await user_repository.create(new_user)
    print(f"User created: {created['email']} with ID: {created['_id']}")
    print("Password is: password123")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
