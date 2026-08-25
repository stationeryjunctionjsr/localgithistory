import os

backend_dir = "backend"
matches = []

for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if ".TABLE" in line or "_dao.TABLE" in line:
                        matches.append((path, line_num, line.strip()))

print(f"Total matches found: {len(matches)}")
for match in matches:
    print(f"{match[0]}:{match[1]} -> {match[2]}")
