"""
Oracle Database Index Creation Script for sj_products and related tables.

Run this ONCE against your Oracle database to create performance indexes.
These indexes dramatically speed up the most common product queries:
- Filter by category, brand, sub_category
- Sort by price (mrp) or date (created_at)
- Filter active products (is_active)
- Search by SKU (exact match)

USAGE:
    python -m app.scripts.create_indexes

Or connect to Oracle SQL*Plus and run the SQL statements below directly.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

# Core product table indexes — each targets a column used in WHERE/ORDER BY clauses
# in product_dao.py's _build_query_conditions() and find_paginated()
PRODUCT_INDEXES = [
    # Filtering by is_active (every query uses this unless includeInactive=True)
    "CREATE INDEX IF NOT EXISTS idx_sj_products_is_active ON sj_products(is_active)",
    # Filtering by category (most common filter in the listing page)
    "CREATE INDEX IF NOT EXISTS idx_sj_products_category ON sj_products(category)",
    # Filtering by brand
    "CREATE INDEX IF NOT EXISTS idx_sj_products_brand ON sj_products(LOWER(brand))",
    # Filtering by sub_category
    "CREATE INDEX IF NOT EXISTS idx_sj_products_sub_category ON sj_products(sub_category)",
    # Sorting by price (price_asc / price_desc sort options)
    "CREATE INDEX IF NOT EXISTS idx_sj_products_mrp ON sj_products(mrp)",
    # Sorting by newest (default sort)
    "CREATE INDEX IF NOT EXISTS idx_sj_products_created_at ON sj_products(created_at DESC)",
    # Exact SKU lookup (used in search)
    "CREATE INDEX IF NOT EXISTS idx_sj_products_sku ON sj_products(sku)",
    # Composite: active + category — the most common combined filter
    "CREATE INDEX IF NOT EXISTS idx_sj_products_active_category ON sj_products(is_active, category)",
    # Composite: active + brand
    "CREATE INDEX IF NOT EXISTS idx_sj_products_active_brand ON sj_products(is_active, LOWER(brand))",
    # Composite: active + created_at — default listing query
    "CREATE INDEX IF NOT EXISTS idx_sj_products_active_created ON sj_products(is_active, created_at DESC)",
]

# Note: Oracle does not support IF NOT EXISTS natively. Use the try/except pattern below.
PRODUCT_INDEXES_ORACLE = [
    "CREATE INDEX idx_sj_products_is_active ON sj_products(is_active)",
    "CREATE INDEX idx_sj_products_category ON sj_products(category)",
    "CREATE INDEX idx_sj_products_brand ON sj_products(brand)",
    "CREATE INDEX idx_sj_products_sub_category ON sj_products(sub_category)",
    "CREATE INDEX idx_sj_products_mrp ON sj_products(mrp)",
    "CREATE INDEX idx_sj_products_created_at ON sj_products(created_at)",
    "CREATE INDEX idx_sj_products_sku ON sj_products(sku)",
    "CREATE INDEX idx_sj_products_active_category ON sj_products(is_active, category)",
    "CREATE INDEX idx_sj_products_active_brand ON sj_products(is_active, brand)",
    "CREATE INDEX idx_sj_products_active_created ON sj_products(is_active, created_at)",
]


async def create_indexes():
    from app.config.database import get_async_session_factory, use_oracle
    from sqlalchemy import text
    from app.config.settings import settings

    if not use_oracle():
        logger.warning("Oracle not configured — skipping index creation.")
        return

    suffix = getattr(settings, "table_suffix", "")
    table_name = f"sj_products{suffix}"
    indexes_to_create = [
        f"CREATE INDEX idx_sj_products_is_active{suffix} ON {table_name}(is_active)",
        f"CREATE INDEX idx_sj_products_category{suffix} ON {table_name}(category)",
        f"CREATE INDEX idx_sj_products_brand{suffix} ON {table_name}(brand)",
        f"CREATE INDEX idx_sj_products_sub_category{suffix} ON {table_name}(sub_category)",
        f"CREATE INDEX idx_sj_products_mrp{suffix} ON {table_name}(mrp)",
        f"CREATE INDEX idx_sj_products_created_at{suffix} ON {table_name}(created_at)",
        f"CREATE INDEX idx_sj_products_sku{suffix} ON {table_name}(sku)",
        f"CREATE INDEX idx_sj_products_active_category{suffix} ON {table_name}(is_active, category)",
        f"CREATE INDEX idx_sj_products_active_brand{suffix} ON {table_name}(is_active, brand)",
        f"CREATE INDEX idx_sj_products_active_created{suffix} ON {table_name}(is_active, created_at)",
    ]

    factory = get_async_session_factory()
    if not factory:
        logger.error("Could not get database session factory.")
        return

    logger.info("Creating Oracle indexes for %s table...", table_name)

    created = 0
    skipped = 0
    failed = 0

    for sql in indexes_to_create:
        index_name = sql.split("CREATE INDEX ")[1].split(" ON ")[0]
        try:
            async with factory() as session:
                await session.execute(text(sql))
                await session.commit()
            logger.info("  ✓ Created index: %s", index_name)
            created += 1
        except Exception as e:
            err_str = str(e)
            if (
                "ORA-00955" in err_str  # index name already used by another object
                or "ORA-01408" in err_str  # column list is already covered by an existing index
                or "already exists" in err_str.lower()
                or "already indexed" in err_str.lower()
            ):
                logger.info("  ~ Index already exists (skipped): %s", index_name)
                skipped += 1
            else:
                logger.error("  ✗ Failed to create index %s: %s", index_name, err_str)
                failed += 1

    logger.info("Index creation complete: %d created, %d already existed, %d failed.", created, skipped, failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(create_indexes())
