with open("backend/scripts/schema_mysql.sql", "r", encoding="utf-8") as f:
    sql = f.read()

sql = sql.replace("  products    JSON,\n", "")

bundle_products_sql = """
CREATE TABLE IF NOT EXISTS sj_bundle_products (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  bundle_id VARCHAR(64) NOT NULL,
  product_id VARCHAR(64) NOT NULL,
  quantity INT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_bundle_id FOREIGN KEY (bundle_id) REFERENCES sj_bundles(external_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

if "sj_bundle_products" not in sql:
    sql += "\n" + bundle_products_sql

with open("backend/scripts/schema_mysql.sql", "w", encoding="utf-8") as f:
    f.write(sql)
