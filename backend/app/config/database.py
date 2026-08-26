"""
Database configuration for Oracle. Uses single DATABASE_URL.
All access is parameterized; one application user.
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


# DATABASE_URL format: mysql+aiomysql://user:password@host:port/dbname
def get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    # Ensure async driver for SQLAlchemy asyncio
    # if url.startswith("oracle:"):
    #     url = "oracle+oracledb_async:" + url[6:]
    # elif url.startswith("oracle+oracledb:"):
    #     url = "oracle+oracledb_async:" + url[16:]
    # elif not url.startswith("oracle+oracledb_async:") and not url.startswith("mysql"):
    #     pass
    if url.startswith("mysql"):
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            url = url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
    else:
        return url  # leave as-is if already full URL
    return url


DATABASE_URL = get_database_url()
_async_engine = None
_async_session_factory = None


def get_async_engine():
    global _async_engine
    if _async_engine is not None:
        return _async_engine
    if not DATABASE_URL:
        return None

    connect_args = {}
    # wallet_path = os.environ.get("WALLET_PATH")
    # if wallet_path and DATABASE_URL and DATABASE_URL.startswith("oracle"):
    #     connect_args["config_dir"] = wallet_path
    #     connect_args["wallet_location"] = wallet_path
    #     connect_args["wallet_password"] = os.environ.get("WALLET_PASSWORD", "WalletPassword123#")

    import sys

    if "pytest" in sys.modules:
        _async_engine = create_async_engine(
            DATABASE_URL,
            poolclass=NullPool,
            echo=os.environ.get("SQL_ECHO", "").lower() in ("1", "true"),
            connect_args=connect_args,
        )
    else:
        # Use QueuePool for connection pooling in a long-running FastAPI app.
        pool_size = int(os.getenv("DB_POOL_SIZE", 5))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 2))
        
        _async_engine = create_async_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=os.environ.get("SQL_ECHO", "").lower() in ("1", "true"),
            connect_args=connect_args,
        )
    return _async_engine


def get_async_session_factory():
    global _async_session_factory
    if _async_session_factory is not None:
        return _async_session_factory
    engine = get_async_engine()
    if engine is None:
        return None
    _async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    if factory is None:
        raise RuntimeError("DATABASE_URL is not set")
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def use_oracle() -> bool:
    return bool(DATABASE_URL)


def is_oracle() -> bool:
    return False  # Oracle commented out, force False
