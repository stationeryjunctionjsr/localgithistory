import os
import re

app_dir = r'c:\Ecommerce app'
patterns = {
    'hasattr': re.compile(r'\bhasattr\s*\('),
    'getattr': re.compile(r'\bgetattr\s*\('),
    'dict_usage': re.compile(r'\bdict\s*\('),
    'dot_get': re.compile(r'\.get\s*\('),
    'isinstance_dict': re.compile(r'\bisinstance\s*\([^,]+,\s*dict\s*\)'),
    'model_dump': re.compile(r'\.model_dump\s*\('),
    'dot_dict': re.compile(r'\.dict\s*\(')
}

results = {p: [] for p in patterns}

for dirpath, _, files in os.walk(app_dir):
    if 'venv' in dirpath or '.git' in dirpath or 'node_modules' in dirpath: continue
    for filename in files:
        if filename.endswith('.py'):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        for p, regex in patterns.items():
                            if regex.search(line):
                                results[p].append(f"{os.path.relpath(filepath, app_dir)}:{i+1}: {line.strip()}")
            except Exception:
                pass

with open('pydantic_scan_report.md', 'w') as f:
    f.write("# Pydantic Anti-Pattern Scan Report\n\n")
    for p, matches in results.items():
        f.write(f"## {p} ({len(matches)} hits)\n")
        if matches:
            f.write("`\n")
            f.write("\n".join(matches))
            f.write("\n`\n")
        f.write("\n")
