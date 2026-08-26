-- Migration: Create sj_delivery_zones table
-- Run this against your MySQL database to add Zone support for delivery slots.

CREATE TABLE IF NOT EXISTS sj_delivery_zones (
  id                        INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id               VARCHAR(32)  NOT NULL,
  name                      VARCHAR(255) NOT NULL,
  description               VARCHAR(1000),
  pincodes                  LONGTEXT,                    -- JSON array of pincode strings
  default_capacity          INT          NOT NULL DEFAULT 10,
  urgent_delivery_available TINYINT(1)   NOT NULL DEFAULT 0,
  is_active                 TINYINT(1)   NOT NULL DEFAULT 1,
  created_at                DATETIME,
  updated_at                DATETIME,
  CONSTRAINT uq_sj_delivery_zones_external UNIQUE (external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_sj_delivery_zones_active ON sj_delivery_zones (is_active);
