"""
Alembic env.py — configured for Oracle (oracledb sync driver).

Connection URL is read from the DATABASE_URL environment variable (same as
the FastAPI app) so there is a single source of truth for credentials.

Because the project uses raw SQL (no ORM models), autogenerate is disabled.
All future schema changes must be written as explicit op.execute() DDL scripts.

To create a new migration:
    alembic revision -m "add_foo_column_to_sj_products"

To apply pending migrations:
    alembic upgrade head

To check current state:
    alembic current
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Ensure the backend package is importable when running alembic from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import create_engine, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No ORM metadata — all migrations are hand-written DDL via op.execute()
target_metadata = None


def _get_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Copy backend/.env.example to backend/.env and fill in the Oracle connection string."
        )
    # Convert to sync oracledb driver (Alembic doesn't use asyncio)
    url = url.replace("oracle+oracledb://", "oracle+oracledb://")
    # Strip any async-only prefix that may have been added
    url = url.replace("oracle+asyncpg://", "oracle+oracledb://")
    return url


def _get_connect_args() -> dict:
    wallet_path = os.environ.get("WALLET_PATH", "")
    if wallet_path:
        return {
            "config_dir": wallet_path,
            "wallet_location": wallet_path,
            "wallet_password": os.environ.get("WALLET_PASSWORD", "WalletPassword123#"),
        }
    return {}


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting to the DB (useful for review/CI)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Disable transaction wrapping — Oracle DDL is auto-committed
        transaction_per_migration=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to Oracle and run pending migrations."""
    connect_args = _get_connect_args()
    engine = create_engine(
        _get_url(),
        poolclass=pool.NullPool,
        connect_args=connect_args if connect_args else {},
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
