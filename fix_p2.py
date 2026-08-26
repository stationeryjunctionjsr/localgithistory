
# 4. Fix .gitignore (Nested directories)
gi = "C:/Ecommerce app/.gitignore"
with open(gi, "r", encoding="utf-8") as f:
    content = f.read()
adds = "\n# Nested test reports\nbackend/load_tests/reports/\nfrontend/playwright-report/\nfrontend/test-results/\n"
if "backend/load_tests/reports/" not in content:
    with open(gi, "a", encoding="utf-8") as f:
        f.write(adds)
print("Fixed .gitignore nested paths")

# 5. Fix schemas.py duplicates
schemas = "C:/Ecommerce app/backend/app/models/schemas.py"
with open(schemas, "r", encoding="utf-8") as f:
    lines = f.readlines()

# A simple heuristic: if we see the same class name defined again, we cut the file or remove the duplicates.
# Actually, the Ruff output earlier showed:
# Redefinition of unused SearchTagCreate from line 656 -> line 1399
# This implies the file was simply duplicated or appended to itself around line 1399.
# Let's check how many lines the file has and if there's a clear duplication point.
