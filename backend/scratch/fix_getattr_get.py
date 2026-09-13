import os
import glob
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    
    # Pattern 1: obj.prop if getattr(obj, 'prop', None) is not None else default
    # E.g. (data.userSegments if getattr(data, 'userSegments', None) is not None else [])
    # E.g. bool((data.isActive if getattr(data, 'isActive', None) is not None else True))
    
    # We want to replace:
    # `([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+) if getattr\(\1, ['"]\2['"], None\) is not None else ([^)]+)`
    # with `\1.\2 if \1.\2 is not None else \3`
    
    content = re.sub(
        r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+) if getattr\(\1,\s*['\"](?:[a-zA-Z0-9_]+)['\"],\s*None\) is not None else ([^)]+)",
        r"\1.\2 if \1.\2 is not None else \3",
        content
    )

    # Pattern 2: getattr(obj, 'prop', default) -> (obj.prop if obj.prop is not None else default)
    # E.g. getattr(data, 'isActive', True) -> (data.isActive if data.isActive is not None else True)
    # E.g. getattr(r, 'show_in_mobile_homepage', False) -> (r.show_in_mobile_homepage if r.show_in_mobile_homepage is not None else False)
    def repl_getattr_data(m):
        obj = m.group(1)
        prop = m.group(2)
        default = m.group(3)
        if default == 'None':
            return f"{obj}.{prop}"
        return f"({obj}.{prop} if {obj}.{prop} is not None else {default})"

    content = re.sub(r"getattr\(([a-zA-Z0-9_]+),\s*['\"]([a-zA-Z0-9_]+)['\"],\s*([^)]+)\)", repl_getattr_data, content)

    # Pattern 3: getattr(obj, 'prop') -> obj.prop
    content = re.sub(r"getattr\(([a-zA-Z0-9_]+),\s*['\"]([a-zA-Z0-9_]+)['\"]\)", r"\1.\2", content)

    # Pattern 4: ((obj.prop if obj.prop is not None else default)) -> (obj.prop if obj.prop is not None else default)
    # Sometimes parens get doubled up.
    # content = content.replace("((", "(").replace("))", ")") # too risky to do globally, could break valid code

    # Pattern 5: .get() -> .prop where applicable.
    # This one is trickier. If it's `payload.get('productId')`, we can change to `payload.productId if payload.productId is not None else None`.
    # Wait, earlier I proved payload in Pydantic defaults to None or is typed properly. But doing blind `.get()` replacement on ANY dictionary could break things if they are actually python dicts (e.g., query params).
    # Since we are aggressively removing workarounds, I'll let Pydantic handle it.
    # We will skip blind `.get()` replacement to avoid breaking actual dicts, but we will fix `getattr`.

    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed getattr in {filepath}")

for root, _, _ in os.walk("c:/Ecommerce app/backend/app"):
    for f in glob.glob(os.path.join(root, "*.py")):
        fix_file(f)

for root, _, _ in os.walk("c:/Ecommerce app/backend/load_tests"):
    for f in glob.glob(os.path.join(root, "*.py")):
        fix_file(f)

