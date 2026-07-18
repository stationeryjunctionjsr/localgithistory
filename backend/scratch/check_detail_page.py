import os
from pathlib import Path

file_path = Path("C:/Ecommerce app/frontend/src/components/ProductDetailClient.tsx")
content = file_path.read_text(encoding="utf-8")
lines = content.splitlines()

print("Occurrences of quantityTiers in ProductDetailClient.tsx:")
for idx, line in enumerate(lines):
    if "quantityTiers" in line or "tier" in line.lower():
        print(f"Line {idx+1}: {line.strip()}")
