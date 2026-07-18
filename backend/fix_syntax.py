import glob
import re
import os

files = glob.glob('c:/Ecommerce app/backend/app/routers/*.py')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix incomplete decorators that my previous script introduced (e.g. `@router.get(""`)
    # Matches `@router.get("" \n`
    new_content = re.sub(r'^@router\.(get|post|put|delete|patch)\(\"\" *\n', r'', content, flags=re.MULTILINE)
    new_content = re.sub(r'^@router\.(get|post|put|delete|patch)\(\'\' *\n', r'', new_content, flags=re.MULTILINE)
    
    # Also clean up duplicate valid ones
    new_content = re.sub(r'^(@router\.(?:get|post|put|delete|patch)\(\"\"[^\n]*\)\n)+', r'\1', new_content, flags=re.MULTILINE)
    new_content = re.sub(r'^(@router\.(?:get|post|put|delete|patch)\(\'\'[^\n]*\)\n)+', r'\1', new_content, flags=re.MULTILINE)
    
    if new_content != content:
        print(f'Fixed {os.path.basename(file)}')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
