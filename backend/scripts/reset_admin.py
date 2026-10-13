import asyncio
from app.models.schemas import UserInternalUpdate
from app.models.user import UserFilter
from app.repositories.user_repository import user_repository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    u = await user_repository.findOne(UserFilter(role="super_admin"))
    print("Found admin:", u.email)
    h = pwd_context.hash("Password123!")
    await user_repository.update(u.id, UserInternalUpdate(password=h))
    print("Password updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
