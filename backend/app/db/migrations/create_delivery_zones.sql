-- Migration: Create sj_delivery_zones table
-- Run this against your MySQL database to add Zone support for delivery slots.

CREATE TABLE IF NOT EXISTS sj_delivery_zones (
  id                        INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id               VARCHAR(32)  NOT NULL,
  name                      VARCHAR(255) NOT NULL,
  description               VARCHAR(1000),
  default_capacity          INT          NOT NULL DEFAULT 10,
  urgent_delivery_available TINYINT(1)   NOT NULL DEFAULT 0,
  customer_type             VARCHAR(20)  NOT NULL DEFAULT 'retail',  -- 'retail' | 'business' | 'both'
  is_active                 TINYINT(1)   NOT NULL DEFAULT 1,
  created_at                DATETIME,
  updated_at                DATETIME,
  CONSTRAINT uq_sj_delivery_zones_external UNIQUE (external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_sj_delivery_zones_active ON sj_delivery_zones (is_active);

-- Child table: one row per pincode belonging to a zone
CREATE TABLE IF NOT EXISTS sj_delivery_zone_pincodes (
  id         INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  parent_id  INT          NOT NULL,
  pincode    VARCHAR(10)  NOT NULL,
  CONSTRAINT fk_sj_dzp_zone FOREIGN KEY (parent_id) REFERENCES sj_delivery_zones (id) ON DELETE CASCADE,
  INDEX ix_sj_dzp_parent (parent_id),
  INDEX ix_sj_dzp_pincode (pincode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Migration: Add seller_ids to existing sj_delivery_zones table (run once on existing deployments)
ALTER TABLE sj_delivery_zones
  ADD COLUMN IF NOT EXISTS seller_ids LONGTEXT COMMENT 'JSON array of seller ID strings';

-- Migration: Add customer_type column to existing deployments (run once)
ALTER TABLE sj_delivery_zones
  ADD COLUMN IF NOT EXISTS customer_type VARCHAR(20) NOT NULL DEFAULT 'retail'
  COMMENT 'retail | business | both';

