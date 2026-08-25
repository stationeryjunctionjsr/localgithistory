filepath = r"c:\Ecommerce app\backend\scripts\schema_mysql.sql"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Find the marker
marker = "-- ============================================================\n-- EXTRA DOCUMENT STORE TABLES\n-- ============================================================"
idx = content.find(marker)

if idx != -1:
    new_content = (
        content[:idx]
        + """-- ============================================================
-- EXTRA RELATIONAL TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS sj_availability_requests (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  product_id VARCHAR(255) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  pincode VARCHAR(32) NOT NULL,
  user_name VARCHAR(255),
  user_email VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_commission_settings (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  default_commission_pct DECIMAL(5,2) NOT NULL DEFAULT 5.0,
  tiers JSON, -- List of commission tiers
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_pincode_searches (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  pincode VARCHAR(32) NOT NULL,
  query VARCHAR(255),
  is_serviceable TINYINT(1) DEFAULT 0,
  timestamp DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_seller_requests (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  request_number VARCHAR(128) NOT NULL,
  user_id VARCHAR(64),
  subject VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  category VARCHAR(64) DEFAULT 'general',
  priority VARCHAR(64) DEFAULT 'medium',
  status VARCHAR(64) DEFAULT 'open',
  attachments JSON,
  responses JSON,
  resolved_at DATETIME,
  closed_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_system_settings (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  maintenance_mode TINYINT(1) DEFAULT 0,
  allow_signups TINYINT(1) DEFAULT 1,
  max_upload_size_mb INT DEFAULT 10,
  default_currency VARCHAR(16) DEFAULT 'INR',
  timezone VARCHAR(64) DEFAULT 'Asia/Kolkata',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_valet_availability (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  date DATE NOT NULL,
  availability_type VARCHAR(64) NOT NULL,
  slots JSON,
  zones JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_valet_payout_settings (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(64) NOT NULL UNIQUE,
  delivery_charge_per_order DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  return_pickup_charge_per_order DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced doc stores with relational schema!")
else:
    print("Marker not found!")
