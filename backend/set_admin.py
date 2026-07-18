import asyncio
import sys
import os

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.repositories.user_repository import user_repository
from app.utils.auth import get_password_hash

async def create_or_update_admin():
    email = os.getenv("TEST_ADMIN_EMAIL", "stationeryjunction.jsr@gmail.com")
    
    password = os.getenv("TEST_ADMIN_PASSWORD")
    if not password:
        import secrets
        password = secrets.token_urlsafe(12)
        print(f"[*] TEST_ADMIN_PASSWORD not set in environment. Generated secure random password: {password}")

    # Check if user already exists
    existing = await user_repository.findByEmail(email)
    if existing:
        print(f"User {email} already exists.")
        await user_repository.update(existing["_id"], {"password": password, "role": "super_admin", "approvalStatus": "approved"})
        print(f"Password reset to '{password}' and role set to super_admin.")
        return

    new_user = {
        "name": "Stationery Junction Admin",
        "email": email,
        "password": get_password_hash(password),
        "role": "super_admin",
        "isActive": True,
        "phone": "9999999999",
        "approvalStatus": "approved",
    }

    created = await user_repository.create(new_user)
    print(f"User created: {created['email']} with ID: {created['_id']}")
    print(f"Password is: {password}")

if __name__ == "__main__":
    asyncio.run(create_or_update_admin())
