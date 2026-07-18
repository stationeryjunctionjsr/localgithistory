import os
import re

db_dir = "backend/app/db"
results = {}

for root, dirs, files in os.walk(db_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Find sj_ tables
                sj_matches = re.findall(r'[\'"](sj_[a-zA-Z0-9_]+)[\'"]', content)
                # Also find TABLE = matches
                table_matches = re.findall(r'TABLE\s*=\s*[\'"]([a-zA-Z0-9_]+)[\'"]', content)
                # Also check uppercase SJ_ tables
                sj_upper_matches = re.findall(r'[\'"](SJ_[a-zA-Z0-9_]+)[\'"]', content)
                all_matches = set(sj_matches + table_matches + sj_upper_matches)
                if all_matches:
                    results[path] = sorted(list(all_matches))

for path, matches in sorted(results.items()):
    print(f"{path}: {matches}")
