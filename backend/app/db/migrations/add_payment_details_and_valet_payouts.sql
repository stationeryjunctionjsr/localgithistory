-- Add bank details to sj_users (for both sellers AND valets)
ALTER TABLE sj_users
  ADD COLUMN bank_account_number VARCHAR(50) DEFAULT NULL,
  ADD COLUMN bank_ifsc_code VARCHAR(20) DEFAULT NULL,
  ADD COLUMN bank_account_holder VARCHAR(255) DEFAULT NULL,
  ADD COLUMN bank_name VARCHAR(255) DEFAULT NULL;

-- Add status + payment tracking to sj_seller_payouts
ALTER TABLE sj_seller_payouts
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
  ADD COLUMN payment_method VARCHAR(32) DEFAULT NULL,
  ADD COLUMN payment_reference VARCHAR(255) DEFAULT NULL,
  ADD COLUMN admin_paid_at DATETIME DEFAULT NULL,
  ADD COLUMN admin_paid_by VARCHAR(64) DEFAULT NULL,
  ADD COLUMN seller_received_at DATETIME DEFAULT NULL;

-- Create valet payout ledger table (mirrors sj_seller_payouts shape)
CREATE TABLE IF NOT EXISTS sj_valet_payouts (
  id INT NOT NULL AUTO_INCREMENT,
  external_id VARCHAR(32) NOT NULL,
  valet_id VARCHAR(64) NOT NULL,
  amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  delivery_count INT NOT NULL DEFAULT 0,
  return_count INT NOT NULL DEFAULT 0,
  period_start DATETIME DEFAULT NULL,
  period_end DATETIME DEFAULT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
  payment_method VARCHAR(32) DEFAULT NULL,
  payment_reference VARCHAR(255) DEFAULT NULL,
  notes TEXT,
  admin_paid_at DATETIME DEFAULT NULL,
  admin_paid_by VARCHAR(64) DEFAULT NULL,
  valet_received_at DATETIME DEFAULT NULL,
  created_at DATETIME DEFAULT NULL,
  updated_at DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY external_id (external_id),
  KEY ix_valet_payouts_valet (valet_id),
  KEY ix_valet_payouts_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
