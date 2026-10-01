import re

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

    pattern_bracket = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[[0-9]+\])?)\s*\[\s*["\']([a-zA-Z0-9_]+)["\']\s*\]')
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
        
    pattern_get = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[[0-9]+\])?)\.get\(\s*["\']([a-zA-Z0-9_]+)["\']\s*\)')
    line = pattern_get.sub(repl_get, line)
    
    return line

with open('pytest_out4.txt', 'r', encoding='utf-8') as f:
    log = f.read()

failures = {}
# Find traceback lines that look like:
# E       TypeError: 'Product' object is not subscriptable
# E       AttributeError: 'OrderInternal' object has no attribute 'get'
# And the filename and line number.
# Pytest format:
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
# tests\test_name.py:123: in test_func
#    n1["isRead"] = True
# E  TypeError: 'NotificationInternal' object is not subscriptable

# Better to just use regex to find the file and line:
lines = log.split('\n')
for i, line in enumerate(lines):
    if line.startswith('E       TypeError: \'') and 'object is not subscriptable' in line:
        # traverse back to find file and line
        j = i - 1
        while j >= 0:
            if re.match(r'.*\.py:\d+:.*', lines[j]) or re.match(r'.*\.py:\d+:', lines[j]):
                # found file and line
                m = re.search(r'([a-zA-Z0-9_/\\]+\.py):(\d+):', lines[j])
                if m:
                    file = m.group(1)
                    lineno = int(m.group(2))
                    failures.setdefault(file, set()).add(lineno)
                    break
            j -= 1
    elif line.startswith('E       AttributeError: \'') and 'object has no attribute \'get\'' in line:
        j = i - 1
        while j >= 0:
            if re.match(r'.*\.py:\d+:.*', lines[j]) or re.match(r'.*\.py:\d+:', lines[j]):
                m = re.search(r'([a-zA-Z0-9_/\\]+\.py):(\d+):', lines[j])
                if m:
                    file = m.group(1)
                    lineno = int(m.group(2))
                    failures.setdefault(file, set()).add(lineno)
                    break
            j -= 1
    elif line.startswith('E       AttributeError: \'dict\' object has no attribute'):
        # This one is tricky, could be dict access where it expects model
        pass

for file, lines_to_fix in failures.items():
    # normalize path
    file = file.replace('\\', '/')
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.readlines()
        for lineno in lines_to_fix:
            content[lineno - 1] = fix_line(content[lineno - 1])
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"Fixed {file} lines {lines_to_fix}")
    except Exception as e:
        print(f"Error {file}: {e}")

