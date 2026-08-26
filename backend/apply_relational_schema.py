from sqlalchemy import create_engine, text

urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}

tables = [
    "sj_stock_reservations",
    "sj_product_notifications",
    "sj_product_reviews",
    "sj_classification_tags",
    "sj_review_classifications",
    "sj_bundles",
    "sj_customer_segments",
    "sj_faq_sections",
    "sj_about_us",
    "sj_privacy_policy",
    # the other 7 tables to ensure they are created
    "sj_availability_requests",
    "sj_commission_settings",
    "sj_pincode_searches",
    "sj_seller_requests",
    "sj_system_settings",
    "sj_valet_availability",
    "sj_valet_payout_settings",
]


def execute_sql_file():
    with open("backend/scripts/schema_mysql.sql", "r", encoding="utf-8") as f:
        sql = f.read()

    # extract create table statements
    statements = []
    current_statement = []
    for line in sql.split("\n"):
        if line.strip().startswith("--"):
            continue
        if line.strip():
            current_statement.append(line)
            if line.strip().endswith(";"):
                statements.append("\n".join(current_statement))
                current_statement = []

    # only care about the specific tables
    table_statements = {}
    for stmt in statements:
        if "CREATE TABLE IF NOT EXISTS" in stmt:
            for t in tables:
                if f"CREATE TABLE IF NOT EXISTS {t}" in stmt:
                    table_statements[t] = stmt
                    break

    for db_name, url in urls.items():
        print(f"Connecting to {db_name}...")
        engine = create_engine(url)
        with engine.connect() as conn:
            for t in tables:
                if t in table_statements:
                    print(f"  Dropping table {t} (if exists)...")
                    conn.execute(text(f"DROP TABLE IF EXISTS {t};"))
                    print(f"  Creating table {t}...")
                    conn.execute(text(table_statements[t]))
            conn.commit()
        print(f"Finished updating {db_name}.")


if __name__ == "__main__":
    execute_sql_file()
