import os
import re

target_dir = r'c:\Ecommerce app\backend\app'

violations = {
    'get()': [],
    'getattr()': [],
    'hasattr()': [],
    'row_to_dict': [],
    'model_dump()': [],
    'json.loads': [],
    'dict_type': [],  # Dict, dict
    'dict_cast': [],  # dict(
    'literal_dict': [], # { "key": value }
    'defaultdict': []
}

# Regexes
re_get = re.compile(r'(?<!router)(?<!requests)(?<!client)(?<!session)(?<!self)(?<!\bapp)\.get\(')
re_getattr = re.compile(r'\bgetattr\(')
re_hasattr = re.compile(r'\bhasattr\(')
re_row_to_dict = re.compile(r'row_to_dict')
re_model_dump = re.compile(r'\.model_dump\(')
re_json_loads = re.compile(r'\bjson\.loads\(')
re_dict_type = re.compile(r'\bDict\b|:\s*dict\b|->\s*dict\b|\bList\[dict\]|\bOptional\[dict\]|\bUnion\[[^\]]*dict\]')
re_dict_cast = re.compile(r'(?<!Config)dict\(')
re_literal_dict = re.compile(r'\{[^{}]*?:[^{}]*?\}') # matches { key: value } roughly
re_defaultdict = re.compile(r'\bdefaultdict\b')

for root, _, files in os.walk(target_dir):
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, target_dir)
        with open(path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file, 1):
                # skip ConfigDict
                if 'ConfigDict' in line: continue
                
                if re_get.search(line): violations['get()'].append(f'{rel}:{i}')
                if re_getattr.search(line): violations['getattr()'].append(f'{rel}:{i}')
                if re_hasattr.search(line): violations['hasattr()'].append(f'{rel}:{i}')
                if re_row_to_dict.search(line): violations['row_to_dict'].append(f'{rel}:{i}')
                if re_model_dump.search(line): violations['model_dump()'].append(f'{rel}:{i}')
                if re_json_loads.search(line): violations['json.loads'].append(f'{rel}:{i}')
                if re_dict_type.search(line): violations['dict_type'].append(f'{rel}:{i}')
                if re_dict_cast.search(line): violations['dict_cast'].append(f'{rel}:{i}')
                if re_defaultdict.search(line): violations['defaultdict'].append(f'{rel}:{i}')
                if re_literal_dict.search(line): violations['literal_dict'].append(f'{rel}:{i}')

for k, v in violations.items():
    print(f'{k}: {len(v)}')
