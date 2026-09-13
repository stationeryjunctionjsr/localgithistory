import ast
import glob
import os
import sys

sys.path.insert(0, 'backend')
from tests.test_router_pydantic_refactor import (
    get_ast_violations_for_file,
    get_signature_violations_for_file,
)

router_files = sorted(glob.glob('backend/app/routers/*.py'))
print(f"Checking {len(router_files)} router files...")

ast_violations_total = 0
sig_violations_total = 0
results = []

for fpath in router_files:
    fname = os.path.basename(fpath)
    if fname == '__init__.py':
        continue
    ast_v = get_ast_violations_for_file(fpath)
    sig_v = get_signature_violations_for_file(fpath)
    ast_count = len(ast_v)
    sig_count = len(sig_v)
    ast_violations_total += ast_count
    sig_violations_total += sig_count
    results.append((fname, ast_count, sig_count, ast_v, sig_v))

print("\n--- SUMMARY OF RESULTS ---")
print(f"Total Router Files checked: {len(results)}")
print(f"Total Category A AST Violations: {ast_violations_total}")
print(f"Total Route Signature Violations: {sig_violations_total}")

for fname, ast_count, sig_count, ast_v, sig_v in results:
    if ast_count > 0 or sig_count > 0:
        print(f"\n[FAIL] {fname}: AST={ast_count}, SIG={sig_count}")
        for v in ast_v:
            print(f"  AST L{v['line']}: {v['caller']}.get({v['args']})")
        for s in sig_v:
            print(f"  SIG L{s['line']}: {s['function']} param {s['param']}: {s['annotation']}")
    else:
        pass

if ast_violations_total == 0 and sig_violations_total == 0:
    print("\nALL ROUTER FILES HAVE ZERO CATEGORY A .get() VIOLATIONS AND ZERO SIGNATURE VIOLATIONS!")
