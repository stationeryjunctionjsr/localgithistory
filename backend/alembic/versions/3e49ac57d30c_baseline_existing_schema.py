"""baseline_existing_schema

Revision ID: 3e49ac57d30c
Revises:
Create Date: 2026-06-09

This is the baseline migration. It represents the 49 Oracle tables that
already exist in production (SJ_USERS, SJ_ORDERS, SJ_PRODUCTS, etc.).

The upgrade/downgrade are intentionally empty — running `alembic stamp head`
against an existing database marks it as being at this revision without
executing any DDL.

All future schema changes (new columns, new tables, index additions) should
be added as new revision files on top of this baseline.

To stamp an existing database:
    alembic stamp head

To create the next migration:
    alembic revision -m "add_logo_url_to_sj_brands"
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "3e49ac57d30c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline — schema already exists. Nothing to run.
    pass


def downgrade() -> None:
    # Cannot undo 49 existing tables. Drop them manually if needed.
    pass
