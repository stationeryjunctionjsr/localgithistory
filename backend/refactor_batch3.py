import os
import glob
import re

files = glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\db\\\\*.py')
files.extend(glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\repositories\\\\*.py'))
files.extend(glob.glob('c:\\\\Ecommerce app\\\\backend\\\\app\\\\config\\\\*.py'))

targets = []
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            if 'table_suffix' in f.read():
                targets.append(file)
    except: pass

print(f"Remaining files with table_suffix: {len(targets)}")

replacements_made = 0
files_modified = []

for filepath in targets:
    if replacements_made >= 10:
        break

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # We will do replacements one by one
    def repl(m):
        global replacements_made
        if replacements_made >= 10:
            return m.group(0) # don't change
        replacements_made += 1
        return '\n        return "' + m.group(1) + '"'

    new_text, count = re.subn(
        r'\s*suffix = \(?settings\.table_suffix.*?\)?\s*\n\s*return f"([^"]+)\{suffix\}"',
        repl,
        text
    )
    
    # Some files use getattr like in mysql_generated_daos.py.bak, we can skip or include.
    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_text)
        files_modified.append(filepath)

print(f'Made {replacements_made} changes across {len(files_modified)} files.')
for f in files_modified:
    print(f)
