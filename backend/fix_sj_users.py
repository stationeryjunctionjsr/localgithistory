from sqlalchemy import create_engine, text

urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}

columns_to_add = [
    "ADD COLUMN is_seller_admin TINYINT(1) NOT NULL DEFAULT 0",
    "ADD COLUMN seller_permissions LONGTEXT",
    "ADD COLUMN service_area_zones LONGTEXT",
    "ADD COLUMN is_on_duty TINYINT(1) NOT NULL DEFAULT 0",
    "ADD COLUMN commission_override_pct DECIMAL(5,2)",
]


def apply_migrations():
    for db_name, url in urls.items():
        print(f"Applying to {db_name}...")
        engine = create_engine(url)
        with engine.begin() as conn:
            for col in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE sj_users {col}"))
                    print(f"  Success: {col}")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"  Skipped (already exists): {col}")
                    else:
                        print(f"  Error: {e}")


if __name__ == "__main__":
    apply_migrations()
    print("Done!")
