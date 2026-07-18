import os
from pathlib import Path

backend_root = Path("C:/Ecommerce app/backend")
results = []
for p in backend_root.rglob("*.py"):
    if "scratch" in p.parts:
        continue
    try:
        content = p.read_text(encoding="utf-8")
        if "coupon_repository" in content or "sj_coupons" in content or "coupons" in content.lower():
            if "seed" in p.name.lower() or "sync" in p.name.lower() or "db" in p.name.lower():
                results.append(str(p))
    except Exception:
        pass

print("Seeding files containing coupon logic:")
for r in results:
    print(" ", r)
