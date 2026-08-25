import os
from pathlib import Path


def inspect_file(file_path):
    print(f"\n=== Inspecting {file_path.name} ===")
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if "id" in line.lower() or "_id" in line:
            if "th" in line.lower() or "td" in line.lower() or "key=" in line.lower():
                print(f"Line {idx + 1}: {line.strip()}")


inspect_file(Path("C:/Ecommerce app/frontend/src/components/Admin/CustomerSegments.tsx"))
inspect_file(Path("C:/Ecommerce app/frontend/src/components/Admin/AdsManager.tsx"))
inspect_file(Path("C:/Ecommerce app/frontend/src/components/Admin/DiscountManagement.tsx"))
