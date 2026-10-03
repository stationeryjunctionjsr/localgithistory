import os
for root, _, files in os.walk("app"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if "bundle_repository.findAll" in line:
                        print(f"{os.path.join(root, f)}: {line.strip()}")
