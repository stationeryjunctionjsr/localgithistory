import os
import re

files = [
    r"c:\Ecommerce app\backend\app\db\mysql_saved_for_later_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_valet_availability_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_tracking_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_product_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_seller_payout_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_seller_request_dao.py"
]

def refactor_get(match):
    obj = match.group(1)
    key = match.group(2)
    default = match.group(3)
    
    if default:
        default_val = default[2:] # skip comma and space
        return f"({obj}[{key}] if {key} in {obj} else {default_val})"
    else:
        return f"({obj}[{key}] if {key} in {obj} else None)"

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # We will replace obj.get("key") and obj.get("key", default)
    # Using a simple regex. 
    # Warning: this regex might be naive, but it fits our exact patterns.
    # Pattern: \b([a-zA-Z_0-9]+)\.get\((['"][a-zA-Z_0-9]+['"])(,\s*[^)]+)?\)
    new_content = re.sub(r'\b([a-zA-Z_0-9]+)\.get\(([\'"][a-zA-Z_0-9_]+[\'"])(,\s*[^)]+)?\)', refactor_get, content)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")

