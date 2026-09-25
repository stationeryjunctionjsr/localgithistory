import os
import re

files_to_process = [
    'app/db/flat_relational_dao.py',
    'app/db/mysql_activities_dao.py',
    'app/db/mysql_banner_dao.py',
    'app/db/mysql_brand_dao.py',
    'app/db/mysql_cart_dao.py',
    'app/db/mysql_categoryTags_dao.py',
    'app/db/mysql_category_dao.py',
    'app/db/mysql_coachMarks_dao.py',
    'app/db/mysql_collections_dao.py',
    'app/db/mysql_commission_settings_dao.py'
]

for filepath in files_to_process:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Pattern:
    # suffix = (settings.table_suffix if settings.table_suffix is not None else "")
    # return f"sj_carts{suffix}"
    # Replace with: return "sj_carts"

    # Also handle table_suffix getattr logic just in case:
    # suffix = getattr(settings, 'table_suffix', '')

    new_text = re.sub(
        r'\s*suffix = \(?settings\.table_suffix.*?\)?\s*\n\s*return f"([^"]+)\{suffix\}"',
        r'\n        return "\1"',
        text
    )
    
    # Catch any other forms? Let's be very safe and just do the exact match.
    # Actually, the regex above will replace the suffix line and the return line.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_text)

print('First 10 files updated.')
