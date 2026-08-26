import re

with open('backend/scripts/schema_mysql.sql', 'r') as f:
    content = f.read()

replacements = [
    (r"CREATE TABLE IF NOT EXISTS sj_customer_segments \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_customer_segments (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  type        VARCHAR(64),\n  name        VARCHAR(255)    NOT NULL,\n  description TEXT,\n  criteria    JSON,\n  is_active   TINYINT(1)      DEFAULT 1,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_product_notifications \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_product_notifications (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  product_id  VARCHAR(64)     NOT NULL,\n  user_id     VARCHAR(64),\n  email       VARCHAR(255),\n  phone       VARCHAR(32),\n  status      VARCHAR(32)     NOT NULL DEFAULT 'pending',\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_product_reviews \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_product_reviews (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  product_id  VARCHAR(64)     NOT NULL,\n  user_id     VARCHAR(64)     NOT NULL,\n  rating      INT             NOT NULL,\n  review_text TEXT,\n  status      VARCHAR(32)     NOT NULL DEFAULT 'pending',\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_review_classifications \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_review_classifications (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  review_id   VARCHAR(64)     NOT NULL,\n  category    VARCHAR(128),\n  confidence_score DECIMAL(5,4),\n  sentiment   VARCHAR(32),\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_stock_reservations \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_stock_reservations (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  product_id  VARCHAR(64)     NOT NULL,\n  user_id     VARCHAR(64),\n  quantity    INT             NOT NULL DEFAULT 1,\n  status      VARCHAR(32)     NOT NULL DEFAULT 'reserved',\n  expires_at  DATETIME,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_bundles \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_bundles (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  name        VARCHAR(255)    NOT NULL,\n  description TEXT,\n  price       DECIMAL(10,2)   NOT NULL,\n  discount_percentage DECIMAL(5,2),\n  is_active   TINYINT(1)      DEFAULT 1,\n  products    JSON,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_faq_sections \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_faq_sections (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  title       VARCHAR(255)    NOT NULL,\n  order_index INT             DEFAULT 0,\n  is_active   TINYINT(1)      DEFAULT 1,\n  faqs        JSON,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_about_us \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_about_us (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  title       VARCHAR(255),\n  content     TEXT            NOT NULL,\n  version     VARCHAR(32),\n  is_published TINYINT(1)     DEFAULT 0,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"),

    (r"CREATE TABLE IF NOT EXISTS sj_privacy_policy \([\s\S]*?ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
     "CREATE TABLE IF NOT EXISTS sj_privacy_policy (\n  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  external_id VARCHAR(32)     NOT NULL UNIQUE,\n  version     VARCHAR(32)     NOT NULL,\n  content     TEXT            NOT NULL,\n  effective_date DATE,\n  is_active   TINYINT(1)      DEFAULT 1,\n  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,\n  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
]

for old, new in replacements:
    content, count = re.subn(old, new, content)
    print(f"Replaced {count} instances for a table")

with open('backend/scripts/schema_mysql.sql', 'w') as f:
    f.write(content)
