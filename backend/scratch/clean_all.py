import os
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: **(user if hasattr(user, 'model_dump') else user)
    # Becomes: **user.model_dump(by_alias=True)
    content = re.sub(r'\*\*\(\s*(\w+)\s*if\s*hasattr\(\1,\s*[\'"]model_dump[\'"]\)\s*else\s*\1\s*\)', r'**\1.model_dump(by_alias=True)', content)

    # Pattern: X.Y if hasattr(X, "Y") else X.Z
    # Becomes: X.Y (Assuming they want the primary field, user banned hasattr)
    content = re.sub(r'(\w+)\.(\w+)\s*if\s*hasattr\(\1,\s*[\'"]\2[\'"]\)\s*else\s*\1\.\w+', r'\1.\2', content)

    # Pattern: getattr(X, "Y", None) or (X["Y"] ... )
    content = re.sub(r'getattr\(([^,]+),\s*\"([^\"]+)\"[^\)]*\)\s*or\s*\(\1\[\"\2\"\][^)]+\)', r'\1.\2', content)

    # Pattern: X.Y if hasattr(X, "Y") else ( X["Y"] ... )
    content = re.sub(r'(\w+)\.(\w+)\s*if\s*hasattr\(\1,\s*[\'"]\2[\'"]\)\s*else\s*\(\1\[\"\2\"\][^\)]*\)', r'\1.\2', content)

    # Pattern: getattr(X, "Y", getattr(X, "Z", payload.Z))
    content = re.sub(r'getattr\(([^,]+),\s*\"([^\"]+)\",\s*getattr\(\1,\s*\"[^\"]+\",\s*([^)]+)\)\)', r'\1.\2 if \1.\2 is not None else \3', content)

    # Pattern: getattr(X, "Y", 0.0) -> X.Y
    content = re.sub(r'getattr\(([^,]+),\s*\"([^\"]+)\",\s*[^)]+\)', r'\1.\2', content)

    # Pattern: X["Y"] if isinstance(X, dict) else (getattr(X, "Y", 0)) -> X.Y
    content = re.sub(r'(\w+)\[\"(\w+)\"\] if isinstance\(\1,\s*dict\) and \"\2\" in \1 else\s*\(?\1\.\2', r'\1.\2', content)
    content = re.sub(r'(\w+)\[\"(\w+)\"\] if isinstance\(\1,\s*dict\) and \"\2\" in \1\s*and\s*\1\[\"\2\"\] is not None\s*else\s*\(?\1\.\2', r'\1.\2', content)
    
    # Simple remaining hasattr
    # if hasattr(X, "Y"): -> if X.Y:
    content = re.sub(r'hasattr\(([^,]+),\s*\"([^\"]+)\"\)', r'hasattr(\1, "\2")', content) # wait, we can't do this globally easily, some might be used as boolean. 
    # Actually `hasattr(X, "Y")` -> `True` if it's a Pydantic model and we know it exists.
    # Let's just fix the assignments first.

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk('backend/app/routers'):
    for file in files:
        if file.endswith('.py'):
            clean_file(os.path.join(root, file))

print('Cleaned')
