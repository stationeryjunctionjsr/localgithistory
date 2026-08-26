from sqlalchemy import create_engine, text

urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}

docstore_tables = [
    "sj_commission_settings",
    "sj_valet_availability",
    "sj_valet_payout_settings",
    "sj_pincode_searches",
    "sj_availability_requests",
    "sj_seller_requests",
]


def create_docstore_table(table_name):
    return f"""
CREATE TABLE IF NOT EXISTS {table_name} (
  id          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  external_id VARCHAR(32)     NOT NULL,
  doc         LONGTEXT,
  created_at  DATETIME,
  updated_at  DATETIME,
  CONSTRAINT uq_{table_name}_external UNIQUE (external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


delivery_zones_table = """
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
"""

delivery_zones_index = """
CREATE INDEX IF NOT EXISTS ix_sj_delivery_zones_active ON sj_delivery_zones (is_active);
"""


def setup_db(db_name, url):
    print(f"Setting up {db_name}...")
    engine = create_engine(url)
    with engine.begin() as conn:
        for t in docstore_tables:
            conn.execute(text(create_docstore_table(t)))
            print(f"  - Created {t}")

        conn.execute(text(delivery_zones_table))
        print("  - Created sj_delivery_zones")
        # For MySQL index creation
        try:
            conn.execute(text(delivery_zones_index))
            print("  - Created index ix_sj_delivery_zones_active")
        except Exception as e:
            # MySQL < 8 does not support CREATE INDEX IF NOT EXISTS, ignore if exists
            if "Duplicate key name" not in str(e):
                raise


if __name__ == "__main__":
    setup_db("sjqadb", urls["sjqadb"])
    setup_db("sjuatdb", urls["sjuatdb"])
    print("Done!")
