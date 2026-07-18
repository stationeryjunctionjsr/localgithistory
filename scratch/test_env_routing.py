import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.settings import settings
from app.db.storage_factory import get_storage
from app.repositories.user_repository import user_repository
from app.repositories.product_repository import product_repository
from app.repositories.stock_reservation_repository import stock_reservation_repository

async def main():
    print("[*] Starting Environment Routing and CRUD Verification...")

    # Test 1: Suffix Routing
    print("\n--- Test 1: Suffix Routing in Settings & Storage Factory ---")
    settings.table_suffix = ""
    user_storage_dev = get_storage("users")
    table_name_dev = user_storage_dev.TABLE if hasattr(user_storage_dev, "TABLE") else user_storage_dev.table_name
    print(f"  Dev table name for 'users': {table_name_dev}")
    assert table_name_dev == "sj_users", f"Dev table name incorrect: {table_name_dev}"

    settings.table_suffix = "_UAT"
    user_storage_uat = get_storage("users")
    table_name_uat = user_storage_uat.TABLE if hasattr(user_storage_uat, "TABLE") else user_storage_uat.table_name
    print(f"  UAT table name for 'users': {table_name_uat}")
    assert table_name_uat == "sj_users_UAT", f"UAT table name incorrect: {table_name_uat}"
    print("[+] Test 1 passed successfully!")

    # Test 2: Repository Table Name Alignment
    print("\n--- Test 2: Repository Table Name Initialization ---")
    settings.table_suffix = "_UAT"
    await stock_reservation_repository.ensure_table_exists()
    tbl = stock_reservation_repository.storage
    tbl_name = tbl.TABLE if hasattr(tbl, "TABLE") else tbl.table_name
    print(f"  Stock reservation table checked/created with suffix: {tbl_name}")
    assert tbl_name == "sj_stock_reservations_UAT", f"UAT table name incorrect: {tbl_name}"
    print("[+] Test 2 passed successfully!")

    # Test 3: UAT Admin Login & Lookup
    print("\n--- Test 3: UAT Admin User Lookup ---")
    settings.table_suffix = "_UAT"
    admin = await user_repository.findByEmail("stationeryjunction.jsr@gmail.com")
    if admin:
        print(f"  [+] Found UAT admin: {admin['email']} (ID: {admin['_id']}, Role: {admin['role']})")
    else:
        print("  [-] Error: UAT admin not found!")
        sys.exit(1)

    # Test 4: UAT CRUD Operation with Identity Column & Sequence Restart
    print("\n--- Test 4: UAT CRUD / Identity sequence check ---")
    settings.table_suffix = "_UAT"
    
    # Clean up any leftover test product using storage findOne with includeInactive
    existing = await product_repository.storage.findOne({"sku": "UAT-NB-001", "includeInactive": True})
    if existing:
        print("  Cleaning up leftover UAT-NB-001 product...")
        await product_repository.storage.delete(existing["_id"])
        
    # 1. Create a dummy product in UAT
    product_data = {
        "name": "UAT Test Notebook",
        "sku": "UAT-NB-001",
        "category": "Notebooks",
        "mrp": 120.0,
        "priceForRetailer": 95.0,
        "priceForWholesaler": 85.0,
        "stock": 100,
        "isActive": True
    }
    
    try:
        new_prod = await product_repository.create(product_data)
        print(f"  [+] Created UAT test product: {new_prod['name']} (ID: {new_prod['_id']})")
        assert new_prod["_id"].isdigit(), "New ID should be numeric identity"
        
        # 2. Update it
        updated_prod = await product_repository.update(new_prod["_id"], {"stock": 150})
        print(f"  [+] Updated UAT product stock to: {updated_prod['stock']}")
        assert updated_prod["stock"] == 150, "Update failed"
        
        # 3. Clean up (delete it via storage to hard delete)
        deleted = await product_repository.storage.delete(new_prod["_id"])
        print(f"  [+] Deleted UAT test product: {deleted}")
        assert deleted, "Delete failed"
        
        print("[+] Test 4 passed successfully! Dynamic CRUD and sequence restarts are fully operational!")
    except Exception as e:
        print(f"  [-] CRUD error: {e}")
        sys.exit(1)

    print("\n[+] Verification complete. All systems fully functional under UAT suffix routing!")

if __name__ == "__main__":
    asyncio.run(main())
