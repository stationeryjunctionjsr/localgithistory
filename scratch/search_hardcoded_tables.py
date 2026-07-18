import os
import re

backend_dir = "backend"
matches = []

for root, dirs, files in os.walk(backend_dir):
    # Skip app/db directory, tests, cache directories
    if "app\\db" in root or "app/db" in root or ".pytest_cache" in root or ".ruff_cache" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py") or file.endswith(".sql"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    # search for sj_ (case insensitive) in strings
                    for m in re.finditer(r'[\'"]([sS][jJ]_[a-zA-Z0-9_]+)[\'"]', line):
                        matches.append((path, line_num, line.strip(), m.group(1)))

print(f"Total matches found: {len(matches)}")
for match in matches:
    print(f"{match[0]}:{match[1]} -> {match[2]} (found: {match[3]})")
