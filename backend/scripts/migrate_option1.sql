-- DDL Migration for Option 1 (Strict Relational Normalization)
-- Important: Run this ONCE. MySQL 5.7 does not support IF NOT EXISTS for ADD COLUMN.

-- 1. Normalize sj_seller_availability
ALTER TABLE sj_seller_availability
  ADD COLUMN reason VARCHAR(1024) NULL AFTER end_at,
  ADD COLUMN created_by VARCHAR(64) NULL AFTER reason,
  ADD COLUMN cancelled_at DATETIME NULL AFTER created_by;

-- 2. Normalize sj_sub_orders
ALTER TABLE sj_sub_orders
  ADD COLUMN sub_order_number VARCHAR(64) NULL AFTER external_id,
  ADD COLUMN parent_order_number VARCHAR(64) NULL AFTER parent_order_id,
  ADD COLUMN seller_name VARCHAR(255) NULL AFTER seller_id,
  ADD COLUMN subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00 AFTER user_id,
  ADD COLUMN tax DECIMAL(12,2) NOT NULL DEFAULT 0.00 AFTER subtotal,
  ADD COLUMN shipping DECIMAL(12,2) NOT NULL DEFAULT 0.00 AFTER tax,
  ADD COLUMN delivery_gst DECIMAL(12,2) NOT NULL DEFAULT 0.00 AFTER shipping,
  ADD COLUMN discount DECIMAL(12,2) NOT NULL DEFAULT 0.00 AFTER delivery_gst,
  ADD COLUMN order_type VARCHAR(64) NULL AFTER total,
  ADD COLUMN payment_method VARCHAR(64) NULL AFTER status,
  ADD COLUMN is_urgent_delivery TINYINT(1) NOT NULL DEFAULT 0 AFTER payment_status,
  ADD COLUMN delivery_slot_config_id VARCHAR(64) NULL AFTER is_urgent_delivery,
  ADD COLUMN delivery_slot_id VARCHAR(64) NULL AFTER delivery_slot_config_id,
  ADD COLUMN delivery_slot_date VARCHAR(32) NULL AFTER delivery_slot_id,
  ADD COLUMN notes TEXT NULL AFTER delivery_slot_date,
  ADD COLUMN coupon_code VARCHAR(64) NULL AFTER notes,
  ADD COLUMN coupon_info_type VARCHAR(64) NULL AFTER coupon_code,
  ADD COLUMN coupon_info_value DECIMAL(12,2) NULL AFTER coupon_info_type,
  ADD COLUMN shipping_name VARCHAR(255) NULL AFTER commission_status,
  ADD COLUMN shipping_phone VARCHAR(64) NULL AFTER shipping_name,
  ADD COLUMN shipping_line1 VARCHAR(512) NULL AFTER shipping_phone,
  ADD COLUMN shipping_city VARCHAR(128) NULL AFTER shipping_line1,
  ADD COLUMN shipping_state VARCHAR(128) NULL AFTER shipping_city,
  ADD COLUMN shipping_pincode VARCHAR(32) NULL AFTER shipping_state,
  ADD COLUMN billing_name VARCHAR(255) NULL AFTER shipping_pincode,
  ADD COLUMN billing_phone VARCHAR(64) NULL AFTER billing_name,
  ADD COLUMN billing_line1 VARCHAR(512) NULL AFTER billing_phone,
  ADD COLUMN billing_city VARCHAR(128) NULL AFTER billing_line1,
  ADD COLUMN billing_state VARCHAR(128) NULL AFTER billing_city,
  ADD COLUMN billing_pincode VARCHAR(32) NULL AFTER billing_state,
  ADD COLUMN delivered_at DATETIME NULL AFTER billing_pincode,
  ADD COLUMN dispatched_at DATETIME NULL AFTER delivered_at,
  ADD COLUMN cancelled_at DATETIME NULL AFTER dispatched_at;

-- 3. Create sj_sub_order_items table
CREATE TABLE IF NOT EXISTS sj_sub_order_items (
  id           INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  sub_order_id INT             NOT NULL,
  product_id   VARCHAR(255)    NOT NULL,
  name         VARCHAR(512)    NOT NULL,
  qty          INT             NOT NULL,
  price        DECIMAL(12,2)   NOT NULL,
  FOREIGN KEY (sub_order_id) REFERENCES sj_sub_orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
