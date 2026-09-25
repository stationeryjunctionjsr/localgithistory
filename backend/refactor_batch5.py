import os
import glob
import re

files = glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\db\\\\*.py')
files.extend(glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\repositories\\\\*.py'))

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # Regular pattern
        new_text = re.sub(
            r'\s*suffix = \(?settings\.table_suffix.*?\)?\s*\n\s*return f"([^"]+)\{suffix\}"',
            r'\n        return "\1"',
            text
        )
        # Alternate pattern in mysql_user_dao.py
        new_text = re.sub(
            r"\s*suffix = settings\.table_suffix.*?\n\s*return f'([^']+)\{suffix\}'",
            r"\n        return '\1'",
            new_text
        )
        
        if new_text != text:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_text)
            print(f'Updated {filepath}')
    except: pass
