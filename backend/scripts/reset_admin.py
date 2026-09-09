import asyncio
from app.repositories.user_repository import user_repository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    u = await user_repository.findOne({"role": "super_admin"})
    print("Found admin:", u.get("email"))
    h = pwd_context.hash("Password123!")
    await user_repository.update(str(u.get("_id") or u.get("id")), {"password": h})
    print("Password updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
