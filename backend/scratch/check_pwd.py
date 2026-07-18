import asyncio
import sys
import os

sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.repositories.user_repository import user_repository
from app.utils.auth import verify_password, get_password_hash

async def check():
    email = "stationeryjunction.jsr@gmail.com"
    user = await user_repository.findByEmail(email)
    if not user:
        print("User not found!")
        return

    print("User found in DB:")
    print("Email:", user.get("email"))
    print("Role:", user.get("role"))
    print("Is Active:", user.get("isActive"))
    print("Password Hash from DB:", repr(user.get("password")))

    test_pwd = "AdminPassword123#"
    matched = verify_password(test_pwd, user.get("password", ""))
    print("Direct verification with 'AdminPassword123#':", matched)

    # Let's generate a new hash and verify it to make surebcrypt works as expected
    new_hash = get_password_hash(test_pwd)
    print("Newly generated hash:", repr(new_hash))
    print("Verification of new hash:", verify_password(test_pwd, new_hash))

if __name__ == "__main__":
    asyncio.run(check())
