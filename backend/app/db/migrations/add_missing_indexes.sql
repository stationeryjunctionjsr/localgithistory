-- ============================================================
-- Migration: add_missing_indexes.sql
-- Description: Adds all missing indexes identified in the
--              architecture audit (Oct 2026).
-- Compatible with: MySQL 5.7+, 8.0+, and all cloud variants
-- NOTE: Run once. Re-running will produce "Duplicate key name"
--       warnings on already-created indexes (harmless).
-- ============================================================

-- ============================================================
-- 1. ORDER TABLES
-- ============================================================

-- 1.1 sj_order_items: order_id FK used on EVERY order load.
--     Without this, every order-items fetch is a full table scan.
ALTER TABLE sj_order_items ADD INDEX ix_order_items_order_id (order_id);

-- 1.2 sj_order_valet_declines: parent_id loaded alongside every order.
ALTER TABLE sj_order_valet_declines ADD INDEX ix_order_valet_declines_parent (parent_id);

-- 1.3 sj_orders: filter by assigned_valet (valet dashboard).
ALTER TABLE sj_orders ADD INDEX ix_orders_assigned_valet (assigned_valet);

-- 1.4 sj_orders: filter by pending_valet_id (valet job assignment).
ALTER TABLE sj_orders ADD INDEX ix_orders_pending_valet (pending_valet_id);

-- 1.5 sj_orders: admin status-only filter (no user_id in WHERE).
--     The existing composite (user_id, status, created_at) only
--     helps when user_id is also in the predicate.
ALTER TABLE sj_orders ADD INDEX ix_orders_status_created (status, created_at);

-- 1.6 sj_orders: idempotency_key lookup after INSERT IGNORE.
ALTER TABLE sj_orders ADD INDEX ix_orders_idempotency_key (idempotency_key);

-- ============================================================
-- 2. SUB-ORDER TABLE
-- ============================================================

-- 2.1 JOIN on parent_order_id in analytics queries.
ALTER TABLE sj_sub_orders ADD INDEX ix_sub_orders_parent (parent_order_id);

-- 2.2 Filter by seller_id in seller dashboards.
ALTER TABLE sj_sub_orders ADD INDEX ix_sub_orders_seller (seller_id);

-- ============================================================
-- 3. PRODUCT CHILD TABLES
--    Every product list/detail call fetches these via
--    WHERE product_id IN (...). Without indexes these are
--    full-table scans on every request.
-- ============================================================

ALTER TABLE sj_product_images             ADD INDEX ix_product_images_pid             (product_id);
ALTER TABLE sj_product_videos             ADD INDEX ix_product_videos_pid             (product_id);
ALTER TABLE sj_product_tags               ADD INDEX ix_product_tags_pid               (product_id);
ALTER TABLE sj_product_details            ADD INDEX ix_product_details_pid            (product_id);
ALTER TABLE sj_product_variant_attributes ADD INDEX ix_product_variant_attrs_pid      (product_id);
ALTER TABLE sj_product_variants           ADD INDEX ix_product_variants_pid           (product_id);

-- variant combo attributes are fetched by variant_id after variants are loaded.
ALTER TABLE sj_product_variant_combo_attrs ADD INDEX ix_product_variant_combo_attrs_vid (variant_id);

-- ============================================================
-- 4. PRODUCT SELLERS TABLE
--    Frequently JOINed to filter products by seller.
-- ============================================================

ALTER TABLE sj_product_sellers ADD INDEX ix_product_sellers_pid (product_id);
ALTER TABLE sj_product_sellers ADD INDEX ix_product_sellers_sid (seller_id);

-- ============================================================
-- 5. PRODUCTS TABLE
-- ============================================================

-- Composite for "new arrivals" query: is_active + created_at.
ALTER TABLE sj_products ADD INDEX ix_products_active_created (is_active, created_at);

-- ============================================================
-- 6. COUPONS TABLE
-- ============================================================

-- 6.1 Generated column for case-insensitive code lookup.
--     findByCode uses UPPER(code) — this avoids a function scan.
ALTER TABLE sj_coupons
    ADD COLUMN code_upper VARCHAR(100) GENERATED ALWAYS AS (UPPER(code)) STORED;

ALTER TABLE sj_coupons ADD UNIQUE INDEX ix_coupons_code_upper (code_upper);

-- 6.2 is_active filter used on every coupon list query.
ALTER TABLE sj_coupons ADD INDEX ix_coupons_active (is_active);

-- ============================================================
-- 7. COUPON CHILD TABLES
--    All fetched via WHERE parent_id IN (...) on every
--    coupon load. Full-table scans without these indexes.
-- ============================================================

ALTER TABLE sj_coupon_quantity_tiers    ADD INDEX ix_coupon_tiers_parent      (parent_id);
ALTER TABLE sj_coupon_roles             ADD INDEX ix_coupon_roles_parent       (parent_id);
ALTER TABLE sj_coupon_users             ADD INDEX ix_coupon_users_parent       (parent_id);
ALTER TABLE sj_coupon_categories        ADD INDEX ix_coupon_categories_parent  (parent_id);
ALTER TABLE sj_coupon_applies_to_values ADD INDEX ix_coupon_applies_to_parent  (parent_id);
ALTER TABLE sj_coupon_excluded_products ADD INDEX ix_coupon_excluded_parent    (parent_id);

-- Composite for per-user usage count lookup.
ALTER TABLE sj_coupon_user_usages ADD INDEX ix_coupon_usages_parent_user (parent_id, user_id);

-- ============================================================
-- 8. SESSIONS TABLE
--    Critical: hit on EVERY authenticated request.
-- ============================================================

ALTER TABLE sj_sessions ADD INDEX        ix_sessions_user_id      (user_id);
ALTER TABLE sj_sessions ADD UNIQUE INDEX ix_sessions_refresh_token (refresh_token_id);

-- ============================================================
-- END OF MIGRATION
-- ============================================================
