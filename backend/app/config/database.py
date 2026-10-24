"""
Database configuration for MySQL. Uses single DATABASE_URL (mysql+aiomysql://...).
All access is parameterised; one application user.
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()
load_dotenv("backend/.env")

from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


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


def _register_pre_ping(engine) -> None:
    """Attach a pool checkout listener that replicates pool_pre_ping behaviour.

    SQLAlchemy's built-in pool_pre_ping calls do_ping() → dbapi_connection.ping()
    with no arguments.  AsyncAdapt_aiomysql_connection.ping() requires the
    `reconnect` argument (no default), so the zero-arg call raises a TypeError.

    Instead of patching the library class, we register a checkout event on the
    *sync* pool that explicitly calls ping(False) — same protection, correct
    call signature, no global mutation of third-party code.
    """
    @event.listens_for(engine.sync_engine, "checkout")
    def _ping_on_checkout(dbapi_connection, connection_record, connection_proxy):
        try:
            dbapi_connection.ping(False)  # False = do not auto-reconnect
        except Exception:
            # Raise DisconnectionError so SQLAlchemy discards the stale
            # connection and retries with a fresh one.
            raise DisconnectionError(
                "aiomysql pre-ping failed; connection will be recycled."
            )


def _register_correlation_id(engine) -> None:
    """Prepend a /* req_id=<X-Request-Id> */ comment to every SQL statement.

    This means every query that appears in the MySQL slow-query log will
    carry the originating HTTP request-ID, so you can grep slow_query.log
    for a request-ID from your application logs and find the exact queries
    it executed.

    The comment is injected via SQLAlchemy's sync before_cursor_execute
    event, which fires at the DBAPI level before the driver sends bytes.
    Overhead is a single string concatenation per query — negligible.
    """
    from app.utils.logger import request_id_var  # local import to avoid circular

    @event.listens_for(engine.sync_engine, "before_cursor_execute", retval=True)
    def _inject_req_id(conn, cursor, statement, parameters, context, executemany):
        req_id = request_id_var.get("-")
        if req_id and req_id != "-":
            statement = f"/* req_id={req_id} */ {statement}"
        return statement, parameters


def get_async_engine():
    global _async_engine
    if _async_engine is not None:
        return _async_engine
    if not DATABASE_URL:
        return None

    connect_args = {}

    import sys

    if "pytest" in sys.modules:
        # Pre-ping is intentionally OFF for tests.
        # Tests use short-lived connections — stale-connection protection is
        # not needed, and the checkout event would complicate event-loop scoping.
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
        # pool_pre_ping=False because we implement the same check ourselves via
        # the checkout event registered below (avoids the aiomysql ping() arity bug).
        # PRODUCTION NOTE: With 4 uvicorn workers these defaults yield
        # 4 × (pool_size + max_overflow) = 4 × 45 = 180 total MySQL connections.
        # Ensure MySQL max_connections ≥ 200 BEFORE deploying.
        # Run: SHOW VARIABLES LIKE 'max_connections';
        # Cloud SQL default is 100 — raise it to 300 in the instance settings.
        pool_size = int(os.getenv("DB_POOL_SIZE", 25))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 20))

        _async_engine = create_async_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=False,
            echo=(os.environ.get("SQL_ECHO", "")).lower() in ("1", "true"),
            connect_args=connect_args,
        )
        _register_pre_ping(_async_engine)
        _register_correlation_id(_async_engine)
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

