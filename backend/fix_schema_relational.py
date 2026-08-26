import re

with open("backend/scripts/schema_mysql.sql", "r", encoding="utf-8") as f:
    c = f.read()

# For customerSegments
c = re.sub(
    r"CREATE TABLE IF NOT EXISTS sj_customer_segments \([\s\S]*?\) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
    """CREATE TABLE IF NOT EXISTS sj_customer_segments (
  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(32)     NOT NULL UNIQUE,
  type        VARCHAR(32)     NOT NULL, 
  name        VARCHAR(255)    NOT NULL,
  description TEXT,
  is_active   TINYINT(1)      DEFAULT 1,
  is_system   TINYINT(1)      DEFAULT 0,
  min_avg_order_value DECIMAL(10,2),
  max_avg_order_value DECIMAL(10,2),
  start_date  DATETIME,
  end_date    DATETIME,
  min_order_freq INT,
  max_order_freq INT,
  state       VARCHAR(255),
  district    VARCHAR(255),
  app_user    TINYINT(1),
  behavior    VARCHAR(255),
  role        VARCHAR(64),
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_customer_segment_users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  segment_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_segment_id FOREIGN KEY (segment_id) REFERENCES sj_customer_segments(external_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;""",
    c,
)

# For faqSections
c = re.sub(
    r"CREATE TABLE IF NOT EXISTS sj_faq_sections \([\s\S]*?\) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
    """CREATE TABLE IF NOT EXISTS sj_faq_sections (
  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(32)     NOT NULL UNIQUE,
  title       VARCHAR(255)    NOT NULL,
  order_index INT             DEFAULT 0,
  icon        VARCHAR(255)    DEFAULT 'help-circle-outline',
  is_active   TINYINT(1)      DEFAULT 1,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sj_faq_items (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  section_id VARCHAR(64) NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_faq_section_id FOREIGN KEY (section_id) REFERENCES sj_faq_sections(external_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;""",
    c,
)

with open("backend/scripts/schema_mysql.sql", "w", encoding="utf-8") as f:
    f.write(c)
