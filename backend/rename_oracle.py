import os
import glob

files = glob.glob('app/**/*.py', recursive=True)
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'use_oracle' in content:
        print(f"Updating {file}")
        content = content.replace('use_oracle', 'use_db')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
