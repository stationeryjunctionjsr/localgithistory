with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

import re

# Remove faqSections
c = re.sub(r'"faqSections": _dao\(\s*"sj_faq_sections",[\s\S]*?\),', "", c)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
