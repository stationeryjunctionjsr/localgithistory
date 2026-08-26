import re

from sqlalchemy import create_engine, inspect

url = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb"
engine = create_engine(url)
insp = inspect(engine)
db_tables = set(insp.get_table_names())

schema_file = r"c:\Ecommerce app\backend\scripts\schema_mysql.sql"
with open(schema_file, "r", encoding="utf-8") as f:
    content = f.read()

# Find all CREATE TABLE statements
sql_tables = set(re.findall(r"CREATE TABLE IF NOT EXISTS (sj_[a_zA_Z0-9_]+)", content))

print(f"Tables in DB: {len(db_tables)}")
print(f"Tables in schema_mysql.sql: {len(sql_tables)}")

missing = sql_tables - db_tables
if missing:
    print(f"Missing from DB: {missing}")
else:
    print("All tables from schema_mysql.sql are in the DB.")
