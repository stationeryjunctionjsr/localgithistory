import re

from sqlalchemy import create_engine, text

db_url = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb"


def get_live_schema(engine):
    live_schema = {}
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'sjqadb'")
        )
        for row in result:
            table_name = row[0]
            col_name = row[1]
            if table_name not in live_schema:
                live_schema[table_name] = set()
            live_schema[table_name].add(col_name.lower())
    return live_schema


def parse_sql_schema(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    sql_schema = {}

    # Split by CREATE TABLE
    # Note: Using regex to find CREATE TABLE blocks
    table_blocks = re.split(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)\s*\(", content, flags=re.IGNORECASE
    )

    for i in range(1, len(table_blocks), 2):
        table_name = table_blocks[i]
        block_content = table_blocks[i + 1]

        # We only want the content up to the matching closing parenthesis of the CREATE TABLE.
        # However, a simpler way since there are no nested parens in column definitions (except types like DECIMAL(18,2))
        # is to just split by lines and look for column names.

        # Let's extract just the table body by finding the closing ");" or ") ENGINE"
        body_match = re.search(r"^(.*?)\)\s*(ENGINE|;)", block_content, re.DOTALL | re.IGNORECASE)
        if body_match:
            body = body_match.group(1)
        else:
            body = block_content  # fallback

        columns = set()
        for line in body.split("\n"):
            line = line.strip()
            # Ignore comments, keys, empty lines
            if (
                not line
                or line.startswith("--")
                or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "KEY", "CONSTRAINT", "INDEX"))
            ):
                continue

            # The first word is usually the column name
            parts = line.split()
            if parts:
                col_name = parts[0].strip("`")
                if re.match(r"^[a-zA-Z0-9_]+$", col_name):
                    columns.add(col_name.lower())

        sql_schema[table_name] = columns

    return sql_schema


def run_audit():
    try:
        engine = create_engine(db_url)
        live_schema = get_live_schema(engine)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    sql_schema = parse_sql_schema(r"c:\Ecommerce app\backend\scripts\schema_mysql.sql")

    report = "# Database Schema Audit Report\n\n"

    missing_tables = []
    missing_columns = {}

    for table, expected_cols in sql_schema.items():
        if table not in live_schema:
            missing_tables.append(table)
        else:
            actual_cols = live_schema[table]
            missing_in_db = expected_cols - actual_cols
            if missing_in_db:
                missing_columns[table] = missing_in_db

    if not missing_tables and not missing_columns:
        report += "✅ **The live database is perfectly in sync with `schema_mysql.sql`.**\n"
    else:
        if missing_tables:
            report += "## ❌ Missing Tables\n"
            report += "The following tables exist in `schema_mysql.sql` but were not found in the live database:\n"
            for t in missing_tables:
                report += f"- `{t}`\n"
            report += "\n"

        if missing_columns:
            report += "## ⚠️ Missing Columns\n"
            report += "The following tables are missing columns that are defined in `schema_mysql.sql`:\n"
            for table, cols in missing_columns.items():
                report += f"- **`{table}`** is missing: {', '.join([f'`{c}`' for c in cols])}\n"

    # Also check for extra tables/columns in DB not in schema (optional, but good for completeness)
    extra_tables = [t for t in live_schema if t not in sql_schema]
    if extra_tables:
        report += "\n## ℹ️ Extra Tables in Live DB (Not in schema_mysql.sql)\n"
        for t in extra_tables:
            report += f"- `{t}`\n"

    with open(
        r"c:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\5cffe2a5-183d-4827-b71a-0cd2beb473a3\schema_audit_report.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(report)

    print("Audit complete! Report saved.")


if __name__ == "__main__":
    run_audit()
