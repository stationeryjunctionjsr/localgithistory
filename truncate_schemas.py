lines = open("backend/app/models/schemas.py", "r", encoding="utf-8").readlines()
classes = {}
duplicate_start = -1
for i, line in enumerate(lines):
    if line.startswith("class "):
        cls_name = line.split()[1].split("(")[0].split(":")[0]
        if cls_name in classes:
            print(f"Duplicate found: {cls_name} at line {i + 1} (first at {classes[cls_name] + 1})")
            if duplicate_start == -1:
                duplicate_start = i
        else:
            classes[cls_name] = i

if duplicate_start != -1:
    print(f"Truncating file from line {duplicate_start + 1} onwards (total lines {len(lines)})")
    with open("backend/app/models/schemas.py", "w", encoding="utf-8") as f:
        f.writelines(lines[:duplicate_start])
