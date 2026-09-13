import ast
import glob
import os

routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

print("=== CHECKING FOR request.json() IN ROUTERS ===")
for rf in router_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8") as f:
        content = f.read()
    if "request.json()" in content or ".json()" in content:
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            if ".json()" in line and not line.strip().startswith("#"):
                print(f"{fname}:{idx}: {line.strip()}")

print("\n=== CHECKING ALL .get( IN ROUTERS ===")
get_usages = []
for rf in router_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        if ".get(" in line and not line.strip().startswith("#"):
            stripped = line.strip()
            # filter out @router.get(
            if stripped.startswith("@router.get") or stripped.startswith("@app.get"):
                continue
            get_usages.append((fname, idx, stripped))

print(f"Total non-decorator .get( occurrences: {len(get_usages)}")
by_file = {}
for fname, idx, stripped in get_usages:
    by_file.setdefault(fname, []).append((idx, stripped))

for fname, usages in sorted(by_file.items(), key=lambda x: -len(x[1])):
    print(f"\n{fname}: {len(usages)} occurrences")
    for idx, stripped in usages[:5]:
        print(f"  L{idx}: {stripped}")
    if len(usages) > 5:
        print(f"  ... and {len(usages) - 5} more")
