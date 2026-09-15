import os
import re

target_dir = r"c:\Ecommerce app\backend\app"

counts = {
    "get()": [],
    "getattr()": [],
    "hasattr()": [],
    "row_to_dict": [],
    "model_dump()": [],
    "dict_type_hint": [],
    "dict_cast": [],
    "defaultdict": [],
    "json_loads": []
}

re_get = re.compile(r'(?<!router)(?<!requests)(?<!client)(?<!session)(?<!self)(?<!\bapp)\.get\(')
re_dict_type = re.compile(r'\bDict\b|:\s*dict\b|->\s*dict\b|\bList\[dict\]|\bOptional\[dict\]|\bUnion\[[^\]]*dict\]')
re_dict_cast = re.compile(r'(?<!Config)dict\(')
re_defaultdict = re.compile(r'\bdefaultdict\(')
re_json_loads = re.compile(r'\bjson\.loads\(')

for root, _, files in os.walk(target_dir):
    for f in files:
        if not f.endswith(".py"): continue
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, target_dir)
        with open(path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file, 1):
                # .get()
                if re_get.search(line): 
                    counts["get()"].append(f"{rel_path}:{i}")
                
                # dict casts
                if re_dict_cast.search(line):
                    counts["dict_cast"].append(f"{rel_path}:{i}")

                # dict type hints
                if re_dict_type.search(line):
                    # Exclude ConfigDict
                    if "ConfigDict" not in line:
                        counts["dict_type_hint"].append(f"{rel_path}:{i}")
                        
                # defaultdict
                if re_defaultdict.search(line):
                    counts["defaultdict"].append(f"{rel_path}:{i}")
                    
                # json.loads
                if re_json_loads.search(line):
                    counts["json_loads"].append(f"{rel_path}:{i}")

print("--- SUMMARY ---")
for k, v in counts.items():
    print(f"{k}: {len(v)}")
