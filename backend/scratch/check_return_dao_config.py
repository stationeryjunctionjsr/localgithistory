import asyncio, sys
sys.path.insert(0, ".")

# Check what the DynamicRelationalDAO uses as scalar_map for returnRequests
from app.db.mysql_generated_daos import GENERATED_DAOS
dao = GENERATED_DAOS["returnRequests"]
print("Table:", dao.TABLE)
print("Scalar map:")
for k, v in dao.scalar_map.items():
    print(f"  {k} -> {v}")
print("Child tables:")
for k, v in dao.config["child_tables"].items():
    print(f"  {k} -> table={v[0]}, db_cols={v[1]}, api_cols={v[2]}, is_flat={v[3]}, is_kv={v[4]}")
