import os
import re

db_dir = "backend/app/db"
excluded_files = ["doc_store.py", "typed_doc_dao.py", "session.py", "oracle_utils.py", "__init__.py"]

table_vars = ["TABLE", "SEND_LOG_TABLE", "ITEMS_TABLE", "PAYMENTS_TABLE", "ENTRIES_TABLE"]

for file in os.listdir(db_dir):
    if file in excluded_files or not file.endswith(".py"):
        continue

    path = os.path.join(db_dir, file)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # 1. Check if settings is imported
    if "from app.config.settings import settings" not in content:
        # Find first import block or top of file to insert
        import_match = re.search(r"^(import\s+|from\s+)", content, re.MULTILINE)
        if import_match:
            idx = import_match.start()
            content = content[:idx] + "from app.config.settings import settings\n" + content[idx:]
            modified = True
        else:
            content = "from app.config.settings import settings\n" + content
            modified = True

    # 2. Replace TABLE variables with properties
    for var in table_vars:
        # Match e.g. TABLE = "sj_brands" or TABLE = 'sj_brands'
        pattern = rf'^\s+{var}\s*=\s*[\'"]([a-zA-Z0-9_]+)[\'"]\s*$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        if matches:
            # We replace from end to beginning to keep string indices correct
            for m in reversed(matches):
                tbl_name = m.group(1)
                replacement = (
                    f"\n    @property\n"
                    f"    def {var}(self):\n"
                    f"        suffix = getattr(settings, 'table_suffix', '')\n"
                    f'        return f"{tbl_name}{{suffix}}"\n'
                )
                start, end = m.span()
                content = content[:start] + replacement + content[end:]
                modified = True

    if modified:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Modified {file}")
    else:
        print(f"[-] No modifications needed for {file}")
