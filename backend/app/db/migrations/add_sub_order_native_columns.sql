-- Migration: Add native indexed columns to sj_sub_orders
-- Reason: MySQLSubOrderDAO uses native columns for fast indexed queries
--         instead of JSON_EXTRACT full-table scans.
-- Run once on existing databases. Safe to re-run (IF NOT EXISTS guards).
-- ──────────────────────────────────────────────────────────────────────────────

-- Step 1: Add native columns (no-op if already present on fresh installs)
ALTER TABLE sj_sub_orders
  ADD COLUMN IF NOT EXISTS seller_id         VARCHAR(255)   NULL AFTER external_id,
  ADD COLUMN IF NOT EXISTS status            VARCHAR(50)    NULL DEFAULT 'pending' AFTER seller_id,
  ADD COLUMN IF NOT EXISTS parent_order_id   VARCHAR(255)   NULL AFTER status,
  ADD COLUMN IF NOT EXISTS user_id           VARCHAR(255)   NULL AFTER parent_order_id,
  ADD COLUMN IF NOT EXISTS commission_status VARCHAR(50)    NULL DEFAULT 'unrealized' AFTER user_id,
  ADD COLUMN IF NOT EXISTS payment_status    VARCHAR(50)    NULL DEFAULT 'pending' AFTER commission_status,
  ADD COLUMN IF NOT EXISTS total             DECIMAL(12,2)  NULL AFTER payment_status;

-- Step 2: Backfill from existing doc JSON blobs (only rows not yet backfilled)
UPDATE sj_sub_orders SET
  seller_id         = JSON_UNQUOTE(JSON_EXTRACT(doc, '$.sellerId')),
  status            = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.status')), 'pending'),
  parent_order_id   = JSON_UNQUOTE(JSON_EXTRACT(doc, '$.parentOrderId')),
  user_id           = JSON_UNQUOTE(JSON_EXTRACT(doc, '$.user')),
  commission_status = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.commissionStatus')), 'unrealized'),
  payment_status    = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.paymentStatus')), 'pending'),
  total             = CAST(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.total')), 'null') AS DECIMAL(12,2))
WHERE doc IS NOT NULL
  AND seller_id IS NULL;

-- Step 3: Add indexes
CREATE INDEX IF NOT EXISTS ix_so_seller_status  ON sj_sub_orders (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_so_parent_order   ON sj_sub_orders (parent_order_id);
CREATE INDEX IF NOT EXISTS ix_so_user_id        ON sj_sub_orders (user_id);
CREATE INDEX IF NOT EXISTS ix_so_commission     ON sj_sub_orders (commission_status);
CREATE INDEX IF NOT EXISTS ix_so_status         ON sj_sub_orders (status);
CREATE INDEX IF NOT EXISTS ix_so_created        ON sj_sub_orders (created_at);
