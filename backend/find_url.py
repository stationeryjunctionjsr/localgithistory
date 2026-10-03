import os
for root, _, files in os.walk("app"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                if "mysql+aiomysql" in file.read():
                    print(os.path.join(root, f))
