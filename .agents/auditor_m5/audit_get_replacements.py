import subprocess
import re

diff = subprocess.check_output(['git', 'diff', 'backend/app/routers/'], text=True)

# Parse diff per file
files = diff.split("diff --git a/")
print(f"Total diff file chunks: {len(files) - 1}")

total_get_removed = 0
total_dot_added = 0
examples = []

for chunk in files[1:]:
    lines = chunk.splitlines()
    header = lines[0]
    filepath = header.split(" b/")[0]
    
    removed_gets = []
    added_lines = []
    
    for l in lines:
        if l.startswith("-") and not l.startswith("---"):
            if ".get(" in l:
                removed_gets.append(l[1:].strip())
        elif l.startswith("+") and not l.startswith("+++"):
            added_lines.append(l[1:].strip())
            
    if removed_gets:
        total_get_removed += len(removed_gets)
        examples.append((filepath, len(removed_gets), removed_gets[:3], added_lines[:5]))

print(f"Total .get( calls removed across modified routers: {total_get_removed}")
print("\nSample router breakdowns:")
for fp, cnt, r_sample, a_sample in examples:
    print(f"\n--- {fp} (Removed {cnt} .get calls) ---")
    print("  Removed sample:")
    for r in r_sample:
        print(f"    - {r}")
    print("  Added sample:")
    for a in a_sample[:3]:
        print(f"    + {a}")

