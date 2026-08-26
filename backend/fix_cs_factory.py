with open("backend/app/db/storage_factory.py", "r", encoding="utf-8") as f:
    c = f.read()

import re

# Add import
if "from app.db.mysql_customer_segment_dao import MySQLCustomerSegmentDAO" not in c:
    c = c.replace(
        "from app.db.mysql_faq_section_dao import MySQLFaqSectionDAO",
        "from app.db.mysql_faq_section_dao import MySQLFaqSectionDAO\nfrom app.db.mysql_customer_segment_dao import MySQLCustomerSegmentDAO",
    )

# Add mapping
if '"customerSegments": MySQLCustomerSegmentDAO,' not in c:
    c = c.replace(
        '"faqSections": MySQLFaqSectionDAO,',
        '"faqSections": MySQLFaqSectionDAO,\n    "customerSegments": MySQLCustomerSegmentDAO,',
    )

with open("backend/app/db/storage_factory.py", "w", encoding="utf-8") as f:
    f.write(c)


# Remove customerSegments from configs
with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'"customerSegments": _dao\(\s*"sj_customer_segments",[\s\S]*?\),', "", c)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
