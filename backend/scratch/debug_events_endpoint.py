import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.routers.analytics import record_event
from app.repositories.tracking_repository import tracking_repository
from app.repositories.analytics_repository import analytics_repository

async def debug():
    session_id = "debug_sess_1"
    event = {
        "type": "session_start",
        "sessionId": session_id,
        "payload": {"returning": True}
    }
    
    print("Step 1: Calling record_event directly in Python...")
    try:
        res = await record_event(event, None)
        print("Success! Response:", res)
    except Exception as e:
        print("Error during record_event:", e)

if __name__ == "__main__":
    asyncio.run(debug())
