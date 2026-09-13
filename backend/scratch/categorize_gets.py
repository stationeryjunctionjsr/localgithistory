import ast
import glob
import os

routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

class GetCallVisitor(ast.NodeVisitor):
    def __init__(self, filename, lines):
        self.filename = filename
        self.lines = lines
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            # Target of .get(...)
            target = ast.unparse(node.func.value)
            # Args
            args = [ast.unparse(a) for a in node.args]
            line_str = self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else ""
            
            # Skip @router.get decorators
            if "router.get" in line_str or "@app.get" in line_str:
                self.generic_visit(node)
                return
                
            self.calls.append({
                "line": node.lineno,
                "target": target,
                "args": args,
                "line_str": line_str
            })
        self.generic_visit(node)

all_calls = []
for rf in router_files:
    fname = os.path.basename(rf)
    if fname == "__init__.py":
        continue
    with open(rf, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    try:
        tree = ast.parse(src, filename=rf)
    except Exception as e:
        print(f"Error {fname}: {e}")
        continue
    visitor = GetCallVisitor(fname, lines)
    visitor.visit(tree)
    for c in visitor.calls:
        c["file"] = fname
        all_calls.append(c)

print(f"Total .get() calls found in router function bodies: {len(all_calls)}")

# Categorize calls
header_calls = []
cache_or_map_lookups = []
payload_or_body_calls = []
db_doc_or_internal_calls = []
other_calls = []

for c in all_calls:
    target = c["target"]
    args = c["args"]
    lstr = c["line_str"]
    
    if "headers" in target:
        header_calls.append(c)
    elif target in ("cache", "_guest_rec_cache", "users_map", "user_map", "products_map", "product_map", "valets_map", "sellers_map", "seller_map", "order_map", "taken", "returned_items_qty", "min_versions", "avail_map"):
        cache_or_map_lookups.append(c)
    elif any(p in target for p in ("payload", "event", "data", "body", "order_data", "request_data", "enriched_event", "sdo")):
        payload_or_body_calls.append(c)
    else:
        db_doc_or_internal_calls.append(c)

print(f"\n1. Header lookups (exempt per R1): {len(header_calls)}")
for c in header_calls:
    print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")

print(f"\n2. Dict/Map in-memory lookups (e.g. users_map.get(id)): {len(cache_or_map_lookups)}")
for c in cache_or_map_lookups[:10]:
    print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")
if len(cache_or_map_lookups) > 10:
    print(f"   ... and {len(cache_or_map_lookups) - 10} more")

print(f"\n3. Request payload/body .get() calls (DIRECT TARGET FOR R1/R2/R3): {len(payload_or_body_calls)}")
for c in payload_or_body_calls:
    print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")

print(f"\n4. Internal doc/model/record .get() calls: {len(db_doc_or_internal_calls)}")
by_file_doc = {}
for c in db_doc_or_internal_calls:
    by_file_doc.setdefault(c["file"], []).append(c)
for fn, clist in sorted(by_file_doc.items(), key=lambda x: -len(x[1])):
    print(f"   {fn}: {len(clist)} calls")
    for c in clist[:3]:
        print(f"      L{c['line']}: {c['target']}.get({', '.join(c['args'])})")
