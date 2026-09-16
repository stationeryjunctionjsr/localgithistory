import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/analytics/events", json={
            "type": "page_view",
            "sessionId": "123",
            "page": "/",
            "payload": {}
        })
        print(res.status_code, res.text)

asyncio.run(main())
