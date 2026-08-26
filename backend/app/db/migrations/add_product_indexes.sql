-- Migration: Add missing indexes to sj_products
-- Purpose: Fix full-table scans for stock availability filter and keyword search.
-- Run once. Compatible with all MySQL versions.

-- Index for stock availability filter (stock > 0)
CREATE INDEX ix_sj_products_stock
    ON sj_products(stock);

-- FULLTEXT index for keyword search (replaces LIKE '%token%' full-table scan)
ALTER TABLE sj_products
    ADD FULLTEXT INDEX ft_sj_products_search (name, brand, category);
