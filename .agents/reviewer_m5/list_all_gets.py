import ast
import glob
import os

routers_dir = 'backend/app/routers'
router_files = sorted(glob.glob(os.path.join(routers_dir, '*.py')))

total_calls = 0
exempt_calls = 0
violations = 0

report_lines = []

for fpath in router_files:
    fname = os.path.basename(fpath)
    if fname == '__init__.py':
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=fpath)
    
    file_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            caller = ast.unparse(node.func.value)
            args = ', '.join(ast.unparse(a) for a in node.args)
            line = lines[node.lineno - 1].strip() if 0 <= node.lineno - 1 < len(lines) else ''
            file_calls.append((node.lineno, caller, args, line))
    
    if file_calls:
        report_lines.append(f"\n=== {fname} ({len(file_calls)} .get calls) ===")
        for lineno, caller, args, line in sorted(file_calls, key=lambda x: x[0]):
            total_calls += 1
            # Check exemption
            is_exempt = False
            exemption_reason = ""
            if caller in ("router", "app"):
                is_exempt = True
                exemption_reason = "FastAPI decorator"
            elif caller.endswith(".headers"):
                is_exempt = True
                exemption_reason = "request.headers"
            elif caller.endswith(".query_params"):
                is_exempt = True
                exemption_reason = "request.query_params"
            elif caller.endswith(".cookies"):
                is_exempt = True
                exemption_reason = "request.cookies"
            elif caller.endswith("_repository") or caller == "repository":
                is_exempt = True
                exemption_reason = "DB repository"
            elif caller in ("product_map", "products_map", "users_map", "payments_map", "order_map", "valets_map", "sellers_map", "seller_docs", "seller_delivery_map", "avail_map", "cache", "_guest_rec_cache", "_cart_products_map", "returned_items_qty", "min_versions"):
                is_exempt = True
                exemption_reason = f"In-memory map/cache: {caller}"
            
            if is_exempt:
                exempt_calls += 1
                report_lines.append(f"  [EXEMPT: {exemption_reason}] L{lineno}: {caller}.get({args})")
            else:
                violations += 1
                report_lines.append(f"  [VIOLATION] L{lineno}: {caller}.get({args}) | {line}")

print(f"Total .get calls across all routers: {total_calls}")
print(f"Total Exempt .get calls: {exempt_calls}")
print(f"Total Category A Violations: {violations}")

with open('.agents/reviewer_m5/all_gets_audit.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total .get calls: {total_calls}\nTotal Exempt: {exempt_calls}\nTotal Violations: {violations}\n")
    out.write('\n'.join(report_lines))

print("Audit written to .agents/reviewer_m5/all_gets_audit.txt")
