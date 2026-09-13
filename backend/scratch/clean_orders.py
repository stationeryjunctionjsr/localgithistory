import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: X["Y"] if isinstance(X, dict) and "Y" in X else getattr(X, "Y", default)
    # Becomes: X.Y
    content = re.sub(r'(\w+)\[\"(\w+)\"\] if isinstance\(\1, dict\) and \"\2\" in \1 else getattr\(\1, \"\2\"[^)]*\)', r'\1.\2', content)
    
    # Pattern: getattr(X, "Y", None) or (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
    content = re.sub(r'getattr\(([^,]+),\s*\"([^\"]+)\"[^)]*\)\s*or\s*\(\1\[\"\2\"\] if isinstance\(\1, dict\) and \"\2\" in \1 else [^)]+\)', r'\1.\2', content)
    
    # Pattern: getattr(X, "Y", None) if hasattr(X, "Y") else (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
    content = re.sub(r'getattr\(([^,]+),\s*\"([^\"]+)\"[^)]*\)\s*if\s*hasattr\(\1,\s*\"\2\"\)\s*else\s*\(\1\[\"\2\"\] if isinstance\(\1, dict\) and \"\2\" in \1 else [^)]+\)', r'\1.\2', content)

    # Some boolean ones: bool(...)
    content = re.sub(r'bool\(getattr\(([^,]+),\s*\"([^\"]+)\"[^)]*\)\s*if\s*hasattr\(\1,\s*\"\2\"\)\s*else\s*\(\1\[\"\2\"\] if isinstance\(\1, dict\) and \"\2\" in \1 else [^)]+\)\)', r'bool(\1.\2)', content)

    # Some float ones: float(...)
    content = re.sub(r'float\((\w+)\[\"(\w+)\"\] if isinstance\(\1, dict\) and \"\2\" in \1 else getattr\(\1, \"\2\"[^)]*\)[^)]*\)', r'float(\1.\2)', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

clean_file('backend/app/routers/orders.py')
print('Cleaned')
