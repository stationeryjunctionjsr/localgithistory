import ast
import glob
import os

routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

print("=== CHECKING INLINE BASEMODELS IN ROUTERS ===")
inline_models = {}
for rf in router_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=rf)
    except:
        continue
        
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_pydantic = any(
                (isinstance(b, ast.Name) and b.id == "BaseModel") or
                (isinstance(b, ast.Attribute) and b.attr == "BaseModel")
                for b in node.bases
            )
            if is_pydantic:
                fields = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        f_name = item.target.id
                        f_ann = ast.unparse(item.annotation)
                        fields.append((f_name, f_ann))
                inline_models.setdefault(fname, []).append((node.name, node.lineno, fields))

for fname, models in inline_models.items():
    print(f"\n{fname}: {len(models)} inline models")
    for mname, lno, fields in models:
        dict_fields = [f"{fn}: {fa}" for fn, fa in fields if "dict" in fa.lower() or "any" in fa.lower()]
        dict_note = f" -> HAS DICT FIELDS: {dict_fields}" if dict_fields else ""
        print(f"  L{lno}: {mname} ({len(fields)} fields){dict_note}")
        if dict_fields:
            for fn, fa in fields:
                print(f"     - {fn}: {fa}")
