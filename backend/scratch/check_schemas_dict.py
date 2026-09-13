import ast

with open("app/models/schemas.py", "r", encoding="utf-8") as f:
    tree = ast.parse(f.read())

dict_schemas = []
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        is_pydantic = any(
            (isinstance(b, ast.Name) and "BaseModel" in b.id) or
            (isinstance(b, ast.Attribute) and "BaseModel" in b.attr)
            for b in node.bases
        )
        if is_pydantic:
            dict_fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fn = item.target.id
                    fa = ast.unparse(item.annotation)
                    if "dict" in fa.lower() or "any" in fa.lower():
                        dict_fields.append((fn, fa))
            if dict_fields:
                dict_schemas.append((node.name, node.lineno, dict_fields))

print(f"Total Pydantic models in schemas.py with dict/any fields: {len(dict_schemas)}")
for sname, lno, dfs in dict_schemas:
    print(f"L{lno}: {sname}")
    for fn, fa in dfs:
        print(f"   - {fn}: {fa}")
