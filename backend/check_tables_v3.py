import sys

from sqlalchemy import create_engine, inspect

url = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb"
engine = create_engine(url)
insp = inspect(engine)
db_tables = set(insp.get_table_names())

# try to get all pydantic models from schemas.py
sys.path.insert(0, "c:/Ecommerce app/backend")
import app.models.schemas as schemas

# find all classes that inherit from BaseModel
model_names = set()
for name in dir(schemas):
    obj = getattr(schemas, name)
    if isinstance(obj, type) and hasattr(obj, "model_fields") and name != "BaseModel":
        model_names.add(name)

print(f"Found {len(db_tables)} tables in DB.")
print(f"Found {len(model_names)} Pydantic models in schemas.py.")

# We know the DB has 51 tables and Option 1 migrations are applied.
# Let's list a few new tables to confirm.
print("\nSome tables in DB:")
for t in sorted(db_tables):
    if "seller" in t or "valet" in t or "commission" in t or "payout" in t or "sub_order" in t:
        print(f" - {t}")
