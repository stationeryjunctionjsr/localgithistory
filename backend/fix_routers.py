import os
import glob
import re

router_dir = r'c:/Ecommerce app/backend/app/routers'
files = glob.glob(f'{router_dir}/*.py')

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    # We want to replace `@router.<method>("/"...)` with `@router.<method>(""...)\n@router.<method>("/"...)`
    
    # re.sub with a function to avoid matching if it's already there
    def replacer(match):
        method = match.group(1) # e.g. "get"
        rest = match.group(2) # e.g. ", response_model=...)" or ")"
        
        # We don't want to double up if we run it twice, but we are replacing the exact string.
        # Actually it's safer to just blindly add it and then deduplicate if needed, 
        # but re.sub will replace every instance.
        
        # The full match is `@router.get("/"...)`
        original = match.group(0)
        
        # The new one we want to prepend is `@router.get(""...)`
        new_route = f'@router.{method}(""{rest}'
        
        # If the new_route is already just before original, do not duplicate
        return f'{new_route}\n{original}'
        
    # Match @router.get("/") or @router.get("/", ...)
    # Regex: @router\.(get|post|put|delete|patch)\(\"\/\"([^\n]*)\)
    # Also handle single quotes
    
    pattern_double = re.compile(r'^@router\.(get|post|put|delete|patch)\(\"\/\"([^\n]*)\)', re.MULTILINE)
    pattern_single = re.compile(r"^@router\.(get|post|put|delete|patch)\('\/'([^\n]*)\)", re.MULTILINE)
    
    new_content = pattern_double.sub(replacer, new_content)
    new_content = pattern_single.sub(replacer, new_content)
    
    # We also need to fix any double duplicates if they were generated (e.g. if we already had "" and run it again)
    # Actually since we didn't match the "" in the regex (we only match "/"), 
    # if it previously added "" it will add another one! 
    # Let's fix that by ensuring we don't duplicate.
    
    # Wait, if we replace, it becomes `@router.get("")\n@router.get("/")`
    # If we run it again, it finds `@router.get("/")` and prepends another `@router.get("")`.
    # Let's clean up any triple or double `@router.get("")`
    
    new_content = re.sub(r'(@router\.(?:get|post|put|delete|patch)\(\"\"[^\n]*\)\n)+', r'\1', new_content)
    new_content = re.sub(r"(@router\.(?:get|post|put|delete|patch)\(\'\'[^\n]*\)\n)+", r'\1', new_content)
    
    if new_content != content:
        print(f'Updated {os.path.basename(file)}')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
