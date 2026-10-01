import ast
import re
import glob

def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def fix_dict_access(content):
    def repl_bracket(m):
        prefix = m.group(1)
        obj = m.group(2)
        key = m.group(3)
        
        # Don't touch if it looks like a method call (e.g., .json()["key"])
        if prefix == '.':
            return m.group(0)
            
        # Ignore HTTP response related variables and other non-models
        ignore_vars = {
            'res', 'response', 'resp', 'response_data', 'data', 'payload', 
            'body', 'json_data', 'res_data', 'expected', 'profile', 'd', 'item', 
            'req_body', 'result_data', 'response_json', 'res_json', 'cart_res', 
            'order_res', 'settings', 'config', 'os.environ'
        }
        
        # Strip indexing like list[0] to get the base variable name
        base_obj = re.sub(r'\[.*?\]', '', obj)
        
        if base_obj in ignore_vars:
            return m.group(0)
            
        if 'json' in base_obj or 'res' in base_obj or 'data' in base_obj:
            return m.group(0)

        if key == '_id':
            snake_key = 'id'
        else:
            snake_key = camel_to_snake(key)
            
        return f"{prefix}{obj}.{snake_key}"

    pattern_bracket = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[.*?\])?)\s*\[\s*["\']([a-zA-Z0-9_]+)["\']\s*\]')
    content = pattern_bracket.sub(repl_bracket, content)
    
    def repl_get(m):
        prefix = m.group(1)
        obj = m.group(2)
        key = m.group(3)
        
        if prefix == '.':
            return m.group(0)
            
        base_obj = re.sub(r'\[.*?\]', '', obj)
        
        ignore_vars = {
            'res', 'response', 'resp', 'response_data', 'data', 'payload', 
            'body', 'json_data', 'res_data', 'expected', 'profile', 'd', 'item', 
            'req_body', 'result_data', 'response_json', 'res_json', 'cart_res', 
            'order_res', 'settings', 'config', 'os.environ'
        }
        
        if base_obj in ignore_vars:
            return m.group(0)
            
        if 'json' in base_obj or 'res' in base_obj or 'data' in base_obj:
            return m.group(0)

        if key == '_id':
            snake_key = 'id'
        else:
            snake_key = camel_to_snake(key)
            
        return f"{prefix}{obj}.{snake_key}"
        
    pattern_get = re.compile(r'(^|[^a-zA-Z0-9_])([a-zA-Z0-9_]+(?:\[.*?\])?)\.get\(\s*["\']([a-zA-Z0-9_]+)["\']\s*\)')
    content = pattern_get.sub(repl_get, content)
    
    return content

for f in glob.glob('tests/test_*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        src = file.read()
    try:
        new_src = fix_dict_access(src)
        if new_src != src:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_src)
            print(f"Fixed dict access in {f}")
    except Exception as e:
        print(f"Failed {f}: {e}")

