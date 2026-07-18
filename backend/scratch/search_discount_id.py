import os
from pathlib import Path

file_path = Path("C:/Ecommerce app/frontend/src/components/Admin/DiscountManagement.tsx")
content = file_path.read_text(encoding="utf-8")
lines = content.splitlines()

print("Lines referencing ID fields in DiscountManagement.tsx:")
for idx, line in enumerate(lines):
    if "_id" in line or "id" in line.lower():
        if "width" not in line.lower() and "grid" not in line.lower() and "valid" not in line.lower() and "guid" not in line.lower() and "middle" not in line.lower() and "divider" not in line.lower() and "slider" not in line.lower():
            print(f"Line {idx+1}: {line.strip()}")
