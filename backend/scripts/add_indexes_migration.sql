-- SQL migration script to add missing indexes to sj_products table
-- Note: LOWER() functional indexes are NOT supported on OCI MySQL HeatWave (26.7.0-cloud).
-- Brand/category/name filtering uses LOWER() in queries; the plain column indexes below
-- still benefit range scans. For case-insensitive brand filtering, the FULLTEXT index covers
-- search-based lookups, and the category index covers equality filters.

CREATE INDEX ix_sj_products_subcategory ON sj_products (sub_category);
CREATE INDEX ix_sj_products_mrp ON sj_products (mrp);
