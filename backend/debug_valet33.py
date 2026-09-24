import asyncio
from app.db.storage_factory import get_storage
from app.repositories.user_repository import user_repository
from app.main import app

async def test_find():
    valets = await user_repository.findAll({'role': 'valet', 'isOnDuty': True})
    print(f"Valets found: {len(valets)}")
    for v in valets:
        print(v.model_dump())

asyncio.run(test_find())
