import asyncio
from app.models.schemas import UserCreate

async def test_user_create():
    u = UserCreate(name="Valet", email="valet@test.com", password="pass", role="valet", isOnDuty=True)
    print("UserCreate dump:", u.model_dump())
    print("isOnDuty attribute:", getattr(u, 'isOnDuty', None))

asyncio.run(test_user_create())
