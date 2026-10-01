import re
from collections import defaultdict
import codecs

def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def fix_line(line):
    # Fix obj["key"]
    def repl_bracket(m):
        prefix = m.group(1)
        obj = m.group(2)
        key = m.group(3)
        if key == '_id':
            snake_key = 'id'
        else:
            snake_key = camel_to_snake(key)
        return f"{prefix}{obj}.{snake_key}"

    pattern_bracket = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[.*?\])?)\s*\[\s*["\']([a-zA-Z0-9_]+)["\']\s*\]')
    line = pattern_bracket.sub(repl_bracket, line)
    
    # Fix obj.get("key")
    def repl_get(m):
        prefix = m.group(1)
        obj = m.group(2)
        key = m.group(3)
        if key == '_id':
            snake_key = 'id'
        else:
            snake_key = camel_to_snake(key)
        return f"{prefix}{obj}.{snake_key}"
        
    pattern_get = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[.*?\])?)\.get\(\s*["\']([a-zA-Z0-9_]+)["\']\s*\)')
    line = pattern_get.sub(repl_get, line)
    
    return line

try:
    with codecs.open('pytest_out_final.txt', 'r', encoding='utf-16') as f:
        log = f.read()
except:
    with open('pytest_out_final.txt', 'r', encoding='utf-8') as f:
        log = f.read()

failures = defaultdict(set)

lines = log.splitlines()
for i, line in enumerate(lines):
    if re.search(r"TypeError: '.*' object is not subscriptable", line) or re.search(r"AttributeError: '.*' object has no attribute 'get'", line):
        # Traverse back to find tests\some_file.py:123
        j = i - 1
        while j >= 0:
            m = re.search(r'(tests[/\\][a-zA-Z0-9_/\\]+\.py):(\d+):', lines[j])
            if m:
                file = m.group(1).replace('\\', '/')
                lineno = int(m.group(2))
                failures[file].add(lineno)
                break
            j -= 1

for file, lines_to_fix in failures.items():
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.readlines()
        for lineno in lines_to_fix:
            if lineno <= len(content):
                content[lineno - 1] = fix_line(content[lineno - 1])
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"Fixed {file} lines {sorted(list(lines_to_fix))}")
    except Exception as e:
        print(f"Error {file}: {e}")

