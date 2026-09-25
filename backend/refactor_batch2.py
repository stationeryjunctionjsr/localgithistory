import os
import glob
import re

files = glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\db\\\\*.py')
files.extend(glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\repositories\\\\*.py'))
targets = []
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            if 'table_suffix' in f.read():
                targets.append(file)
    except: pass

print(f"Remaining files with table_suffix: {len(targets)}")

files_to_process = targets[:10]

for filepath in files_to_process:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    new_text = re.sub(
        r'\s*suffix = \(?settings\.table_suffix.*?\)?\s*\n\s*return f"([^"]+)\{suffix\}"',
        r'\n        return "\1"',
        text
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_text)

print('Second batch of 10 files updated.')
