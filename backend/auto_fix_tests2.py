import re
from collections import defaultdict

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

with open('pytest_out4.txt', 'r', encoding='utf-8') as f:
    log = f.read()

failures = defaultdict(set)

# Find all matches of 	ests\some_file.py:123: TypeError or 	ests/some_file.py:123: AttributeError
matches = re.finditer(r'(tests[/\\][a-zA-Z0-9_/\\]+\.py):(\d+):\s*(TypeError|AttributeError)', log)
for m in matches:
    file = m.group(1).replace('\\', '/')
    lineno = int(m.group(2))
    failures[file].add(lineno)

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

