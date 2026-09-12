from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import time

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

APP_START_TIME = time.time()



class LivenessResponse(BaseModel):
    status: str
    uptime_seconds: float
    timestamp: float


class LivenessResponse(BaseModel):
    status: str
    uptime_seconds: float
    timestamp: float


class LivenessResponse(BaseModel):
    status: str
    uptime_seconds: float
    timestamp: float

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    timestamp: float
    db: str


@router.get("/health/live", response_model=LivenessResponse)
async def check_liveness():
    """Lightweight liveness check (no DB). Returns 200 if the process is running."""
    return {"status": "ok", "uptime_seconds": round(time.time() - APP_START_TIME, 2), "timestamp": time.time()}


@router.get("/health", response_model=HealthResponse)
@router.get("/health/ready", response_model=HealthResponse)
async def check_health():
    """
    Readiness check. Checks application liveness and database reachability.
    Returns 200 when healthy, 503 when the database is unreachable.
    """
    from fastapi.responses import JSONResponse
    from sqlalchemy import text

    from app.config.database import get_async_engine, use_oracle

    db_status = "ok"

    if use_oracle():
        try:
            engine = get_async_engine()
            if engine:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1 FROM dual"))
            else:
                db_status = "unconfigured"
        except Exception:
            db_status = "unreachable"
    else:
        # JSON file-based storage — check that the data directory is readable
        try:
            from pathlib import Path

            from app.utils.file_storage import DATA_DIR

            data_path = Path(DATA_DIR)
            if not data_path.exists():
                db_status = "data_dir_missing"
        except Exception:
            db_status = "unreachable"

    payload = HealthResponse(
        status="ok" if db_status in ("ok", "unconfigured") else "degraded",
        uptime_seconds=round(time.time() - APP_START_TIME, 2),
        timestamp=time.time(),
        db=db_status,
    )

    if db_status == "unreachable":
        return JSONResponse(status_code=503, content=payload)

    return payload
