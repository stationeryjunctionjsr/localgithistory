-- Migration: Add composite index on sj_orders for common list query
-- Reason: Every order list endpoint filters by user_id + status and sorts
--         by created_at DESC. Without this index MySQL does a full table
--         scan for every request. The index lets it jump directly to the
--         matching rows, already in sort order.
--
-- Query pattern it covers:
--   SELECT * FROM sj_orders
--   WHERE user_id = ?       -- AND/OR
--     AND status  = ?
--   ORDER BY created_at DESC
--
-- Safe to run on a live table — MySQL builds the index online (no table lock).
-- ──────────────────────────────────────────────────────────────────────────────

CREATE INDEX ix_orders_user_status_created
    ON sj_orders (user_id, status, created_at DESC);
