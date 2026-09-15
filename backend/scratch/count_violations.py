import os
import re

target_dir = r"c:\Ecommerce app\backend\app"

counts = {
    "get()": 0,
    "getattr()": 0,
    "hasattr()": 0,
    "row_to_dict": 0,
    "model_dump()": 0,
    "dict() / Dict": 0,
    "defaultdict": 0,
    "json.loads": 0
}

# Regexes
re_get = re.compile(r'(?<!router)(?<!requests)(?<!client)(?<!session)(?<!self)\.get\(')
re_getattr = re.compile(r'\bgetattr\(')
re_hasattr = re.compile(r'\bhasattr\(')
re_row_to_dict = re.compile(r'row_to_dict')
re_model_dump = re.compile(r'\.model_dump\(')
re_dict = re.compile(r'\bdict\b|\bDict\b')
re_defaultdict = re.compile(r'\bdefaultdict\b')
re_json_loads = re.compile(r'\bjson\.loads\(')

for root, _, files in os.walk(target_dir):
    for f in files:
        if not f.endswith(".py"): continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if re_get.search(line): counts["get()"] += 1
                if re_getattr.search(line): counts["getattr()"] += 1
                if re_hasattr.search(line): counts["hasattr()"] += 1
                if re_row_to_dict.search(line): counts["row_to_dict"] += 1
                if re_model_dump.search(line): counts["model_dump()"] += 1
                if re_dict.search(line): counts["dict() / Dict"] += 1
                if re_defaultdict.search(line): counts["defaultdict"] += 1
                if re_json_loads.search(line): counts["json.loads"] += 1

for k, v in counts.items():
    print(f"{k}: {v}")
