-- Migration: Add Hyperlocal Zone Delivery Charges and Global Hyperlocal Defaults
-- Non-destructive: new columns have defaults or are nullable. New child table created if not exists.

-- 1. sj_delivery_zones: Add zone-level delivery fees and thresholds
ALTER TABLE sj_delivery_zones
  ADD COLUMN delivery_charge DECIMAL(10,2) DEFAULT NULL COMMENT 'Base delivery fee for this zone',
  ADD COLUMN min_cart_value DECIMAL(10,2) DEFAULT NULL COMMENT 'Cart amount threshold for free delivery in this zone',
  ADD COLUMN urgent_delivery_charge DECIMAL(10,2) DEFAULT NULL COMMENT 'Surcharge for urgent delivery slot in this zone',
  ADD COLUMN apply_default_charge TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 = use global hyperlocal default tiers, 0 = use zone custom charge/tiers';

-- 2. sj_delivery_zone_tiers: Child table for zone-level delivery charge tiers
CREATE TABLE IF NOT EXISTS sj_delivery_zone_tiers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  parent_id INT NOT NULL COMMENT 'FK to sj_delivery_zones.id',
  min_order_value VARCHAR(255) DEFAULT '0' COMMENT 'Lower bound cart value',
  max_order_value VARCHAR(255) NOT NULL COMMENT 'Upper bound cart value or Infinity',
  charge VARCHAR(255) NOT NULL COMMENT 'Delivery fee for this tier',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_zone_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. sj_delivery_charge_defaults: Add global fallback delivery rates for hyperlocal orders
ALTER TABLE sj_delivery_charge_defaults
  ADD COLUMN hyperlocal_base_charge DECIMAL(10,2) NOT NULL DEFAULT 40.00 COMMENT 'Fallback base delivery fee for hyperlocal zones',
  ADD COLUMN hyperlocal_free_threshold DECIMAL(10,2) NOT NULL DEFAULT 300.00 COMMENT 'Fallback free delivery threshold for hyperlocal zones',
  ADD COLUMN hyperlocal_urgent_delivery_charge DECIMAL(10,2) DEFAULT 50.00 COMMENT 'Fallback urgent delivery surcharge for hyperlocal zones';
