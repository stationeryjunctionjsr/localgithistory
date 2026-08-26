-- Migration: Convert sj_seller_availability GENERATED columns to regular writeable columns
-- Reason: MySQLSellerAvailabilityDAO writes seller_id/status/start_at/end_at directly.
--         GENERATED ALWAYS AS columns are read-only and would reject those writes.
-- Run AFTER add_seller_availability_columns.sql (which added the GENERATED columns).
-- Safe to run on fresh DBs that haven't run the GENERATED columns migration yet.
-- ──────────────────────────────────────────────────────────────────────────────

-- Step 1: Drop indexes that reference the generated columns
DROP INDEX IF EXISTS ix_sa_status_times  ON sj_seller_availability;
DROP INDEX IF EXISTS ix_sa_seller_status ON sj_seller_availability;

-- Step 2: Drop the GENERATED columns
ALTER TABLE sj_seller_availability
  DROP COLUMN IF EXISTS seller_id,
  DROP COLUMN IF EXISTS status,
  DROP COLUMN IF EXISTS start_at,
  DROP COLUMN IF EXISTS end_at;

-- Step 3: Re-add as regular (writeable) columns
ALTER TABLE sj_seller_availability
  ADD COLUMN seller_id VARCHAR(64)  NULL AFTER external_id,
  ADD COLUMN status    VARCHAR(32)  NULL DEFAULT 'scheduled' AFTER seller_id,
  ADD COLUMN start_at  DATETIME     NULL AFTER status,
  ADD COLUMN end_at    DATETIME     NULL AFTER start_at;

-- Step 4: Backfill from existing doc JSON
UPDATE sj_seller_availability SET
  seller_id = JSON_UNQUOTE(JSON_EXTRACT(doc, '$.sellerId')),
  status    = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.status')), 'scheduled'),
  start_at  = STR_TO_DATE(REPLACE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.startAt')), 'Z', ''), '%Y-%m-%dT%H:%i:%s'),
  end_at    = STR_TO_DATE(REPLACE(JSON_UNQUOTE(JSON_EXTRACT(doc, '$.endAt')),   'Z', ''), '%Y-%m-%dT%H:%i:%s')
WHERE doc IS NOT NULL;

-- Step 5: Re-create indexes
CREATE INDEX ix_sa_status_times  ON sj_seller_availability (status, start_at, end_at);
CREATE INDEX ix_sa_seller_status ON sj_seller_availability (seller_id, status);
