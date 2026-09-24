import asyncio
from app.repositories.user_repository import user_repository
from app.main import app

async def test_find():
    valets = await user_repository.findAll({'role': 'valet'})
    print(f"All valets found: {len(valets)}")
    for v in valets:
        print(v.name, " isOnDuty:", v.isOnDuty, " email:", v.email)

asyncio.run(test_find())
