"""
Database configuration for MySQL. Uses single DATABASE_URL (mysql+aiomysql://...).
All access is parameterised; one application user.
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Patch AsyncAdapt_aiomysql_connection.ping for compatibility with SQLAlchemy / PyMySQL:
# In PyMySQL >= 1.1 / 2.0, Connection.ping() defaults to reconnect=False.
# SQLAlchemy's MySQLDialect_pymysql.do_ping() calls dbapi_connection.ping() without
# arguments when PyMySQL's default is reconnect=False.
# However, AsyncAdapt_aiomysql_connection.ping(self, reconnect: bool) omitted the
# default value (= False), raising a TypeError when pool_pre_ping=True checks out a connection.
try:
    from sqlalchemy.dialects.mysql.aiomysql import AsyncAdapt_aiomysql_connection
    _orig_aiomysql_ping = AsyncAdapt_aiomysql_connection.ping

    def _safe_aiomysql_ping(self, reconnect: bool = False) -> None:
        return _orig_aiomysql_ping(self, reconnect)

    AsyncAdapt_aiomysql_connection.ping = _safe_aiomysql_ping
except Exception:
    pass


# DATABASE_URL format: mysql+aiomysql://user:password@host:port/dbname
def get_database_url() -> str | None:
    url = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else None
    if not url:
        return None
    # Ensure async driver for SQLAlchemy asyncio
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

    import sys

    if "pytest" in sys.modules:
        # pool_pre_ping is intentionally OFF for tests.
        # AsyncAdapt_aiomysql_connection.ping() is not compatible with the way
        # pytest-asyncio manages the event loop, causing test failures.
        # Tests use short-lived connections — pre-ping is not needed.
        _async_engine = create_async_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=(os.environ.get("SQL_ECHO", "")).lower() in ("1", "true"),
            connect_args=connect_args,
        )
    else:
        # Use QueuePool for connection pooling in a long-running FastAPI app.
        # pool_pre_ping=True protects against stale connections after DB restart
        # or long idle periods (safe for the production async loop).
        pool_size = int(os.getenv("DB_POOL_SIZE", 5))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 2))

        _async_engine = create_async_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=(os.environ.get("SQL_ECHO", "")).lower() in ("1", "true"),
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


async def get_session():
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

