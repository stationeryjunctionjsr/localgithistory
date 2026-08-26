with open("backend/app/db/storage_factory.py", "r", encoding="utf-8") as f:
    c = f.read()


# Add import
if "from app.db.mysql_faq_section_dao import MySQLFaqSectionDAO" not in c:
    c = c.replace(
        "from app.db.mysql_bundle_dao import MySQLBundleDAO",
        "from app.db.mysql_bundle_dao import MySQLBundleDAO\nfrom app.db.mysql_faq_section_dao import MySQLFaqSectionDAO",
    )

# Add mapping
if '"faqSections": MySQLFaqSectionDAO,' not in c:
    c = c.replace('"bundles": MySQLBundleDAO,', '"bundles": MySQLBundleDAO,\n    "faqSections": MySQLFaqSectionDAO,')

with open("backend/app/db/storage_factory.py", "w", encoding="utf-8") as f:
    f.write(c)
