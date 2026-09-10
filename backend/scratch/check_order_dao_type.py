import asyncio, sys
sys.path.insert(0, ".")
from app.db.storage_factory import get_storage, GENERATED_DAOS, _MYSQL_DAO_COLLECTIONS

s = get_storage("orders")
print("orders DAO type:", type(s).__name__)
print("In GENERATED_DAOS:", "orders" in GENERATED_DAOS)
print("In _MYSQL_DAO_COLLECTIONS:", "orders" in _MYSQL_DAO_COLLECTIONS)
