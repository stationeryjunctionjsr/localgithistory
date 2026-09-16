import asyncio
import traceback
from httpx import AsyncClient, ASGITransport
from app.main import app
import signal
import sys

async def main():
    def handler(sig, frame):
        print("Got timeout!")
        traceback.print_stack(frame)
        sys.exit(0)
    
    # We can't use signal.alarm on Windows.
    async def fetch():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/bundles/product/1")
            print(res.status_code, res.text)
            
    try:
        await asyncio.wait_for(fetch(), timeout=5)
    except asyncio.TimeoutError:
        print("Timeout! Let's print tasks")
        for task in asyncio.all_tasks():
            print("--- TASK ---")
            task.print_stack()

asyncio.run(main())
