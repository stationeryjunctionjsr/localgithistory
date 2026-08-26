from sqlalchemy import create_engine, inspect

# Connection URLs
urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}


def check_db(db_name, url):
    print(f"\n--- Tables in {db_name} ---")
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        db_tables = inspector.get_table_names()

        for t in sorted(db_tables):
            print(f"  - {t}")

    except Exception as e:
        print(f"Failed to connect or inspect {db_name}: {e}")


if __name__ == "__main__":
    check_db("sjqadb", urls["sjqadb"])
    check_db("sjuatdb", urls["sjuatdb"])
