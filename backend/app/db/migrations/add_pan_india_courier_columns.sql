-- Migration: Add Pan-India courier fulfillment columns to orders, sub-orders, products, and delivery defaults
-- Safe and non-destructive: all new columns have default values or are nullable.

-- 1. Orders: Add courier & national fulfillment columns
ALTER TABLE sj_orders
  ADD COLUMN IF NOT EXISTS fulfillment_type VARCHAR(20) NOT NULL DEFAULT 'hyperlocal' COMMENT 'hyperlocal | courier',
  ADD COLUMN IF NOT EXISTS courier_partner VARCHAR(64) DEFAULT NULL COMMENT 'Courier service name (e.g. Delhivery, Shiprocket, Blue Dart)',
  ADD COLUMN IF NOT EXISTS tracking_id VARCHAR(64) DEFAULT NULL COMMENT 'Courier tracking ID / order ID',
  ADD COLUMN IF NOT EXISTS awb_code VARCHAR(64) DEFAULT NULL COMMENT 'Air Waybill number from courier',
  ADD COLUMN IF NOT EXISTS shipping_label_url VARCHAR(500) DEFAULT NULL COMMENT 'URL or file path to generated printable AWB shipping label PDF',
  ADD COLUMN IF NOT EXISTS estimated_delivery_date DATETIME DEFAULT NULL COMMENT 'Expected delivery date calculated by courier';

-- 2. Sub-orders: Add fulfillment and tracking columns for parity
ALTER TABLE sj_sub_orders
  ADD COLUMN IF NOT EXISTS fulfillment_type VARCHAR(20) NOT NULL DEFAULT 'hyperlocal' COMMENT 'hyperlocal | courier',
  ADD COLUMN IF NOT EXISTS courier_partner VARCHAR(64) DEFAULT NULL COMMENT 'Courier service name',
  ADD COLUMN IF NOT EXISTS tracking_id VARCHAR(64) DEFAULT NULL COMMENT 'Courier tracking ID',
  ADD COLUMN IF NOT EXISTS awb_code VARCHAR(64) DEFAULT NULL COMMENT 'Air Waybill number';

-- 3. Products: Add physical weight & dimensions for 3PL freight calculation + HSN for GST
ALTER TABLE sj_products
  ADD COLUMN IF NOT EXISTS weight_grams INT NOT NULL DEFAULT 200 COMMENT 'Gross weight in grams',
  ADD COLUMN IF NOT EXISTS length_cm DECIMAL(6,2) DEFAULT NULL COMMENT 'Package length in cm',
  ADD COLUMN IF NOT EXISTS width_cm DECIMAL(6,2) DEFAULT NULL COMMENT 'Package width in cm',
  ADD COLUMN IF NOT EXISTS height_cm DECIMAL(6,2) DEFAULT NULL COMMENT 'Package height in cm',
  ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(16) DEFAULT NULL COMMENT 'HSN code for GST invoices & courier e-way bills';

-- 4. Delivery Charge Defaults: Baseline national courier shipping fees
ALTER TABLE sj_delivery_charge_defaults
  ADD COLUMN IF NOT EXISTS courier_base_charge DECIMAL(10,2) NOT NULL DEFAULT 60.00 COMMENT 'Flat standard courier shipping fee',
  ADD COLUMN IF NOT EXISTS courier_free_threshold DECIMAL(10,2) NOT NULL DEFAULT 499.00 COMMENT 'Order value threshold for free courier shipping';
