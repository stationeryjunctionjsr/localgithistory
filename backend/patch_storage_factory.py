import re

with open("backend/app/db/storage_factory.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add import for MySQLBundleDAO
if "from app.db.mysql_bundle_dao import MySQLBundleDAO" not in content:
    content = content.replace(
        "from app.db.mysql_doc_store import MySQLDocStore",
        "from app.db.mysql_doc_store import MySQLDocStore\nfrom app.db.mysql_bundle_dao import MySQLBundleDAO",
    )

# Remove the lambda references for the 15 tables
tables_to_remove = [
    "stockReservations",
    "productNotifications",
    "productReviews",
    "reviewClassifications",
    "bundles",
    "customerSegments",
    "faqSections",
    "aboutUs",
    "privacyPolicy",
    "commissionSettings",
    "valetAvailability",
    "valetPayoutSettings",
    "pincodeSearches",
    "availabilityRequests",
    "systemSettings",
]

for table in tables_to_remove:
    # Remove lines like: "tableName": lambda: MySQLDocStore(...),
    pattern = r'\s*"' + table + r'":\s*lambda:\s*MySQLDocStore\(.*?\),'
    content = re.sub(pattern, "", content)

# Add bundles mapping
if '"bundles": MySQLBundleDAO,' not in content:
    content = re.sub(
        r"_MYSQL_DAO_COLLECTIONS = \{", '_MYSQL_DAO_COLLECTIONS = {\n    "bundles": MySQLBundleDAO,', content
    )

with open("backend/app/db/storage_factory.py", "w", encoding="utf-8") as f:
    f.write(content)
