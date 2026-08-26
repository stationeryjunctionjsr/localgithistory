import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}

scripts = [
    r"c:\Ecommerce app\backend\scripts\add_indexes_migration.sql",
    r"c:\Ecommerce app\backend\scripts\add_indices.sql",
]


def apply_indexes():
    for db_name, url in urls.items():
        print(f"Applying to {db_name}...")
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                for script in scripts:
                    print(f"  Reading {os.path.basename(script)}")
                    with open(script, "r") as f:
                        content = f.read()

                    # Split by ';'
                    statements = [s.strip() for s in content.split(";") if s.strip()]

                    for stmt in statements:
                        if not stmt.upper().startswith("CREATE INDEX"):
                            continue

                        try:
                            conn.execute(text(stmt))
                            print(f"    Success: {stmt.split(' ON ')[0]}")
                        except Exception as e:
                            if "Duplicate key name" in str(e):
                                print(f"    Skipped (already exists): {stmt.split(' ON ')[0]}")
                            else:
                                print(f"    Error executing: {stmt}\n    Reason: {e}")
                conn.commit()
        except OperationalError as e:
            print(f"Could not connect to {db_name}: {e}")


if __name__ == "__main__":
    apply_indexes()
    print("Done applying indexes!")
