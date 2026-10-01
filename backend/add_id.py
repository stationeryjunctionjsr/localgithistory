import glob
import re

for f in glob.glob('tests/test_*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # replace Model(**{ with Model(**{"_id": __import__("uuid").uuid4().hex, **{
    new_content = re.sub(r'([A-Za-z]+InternalCreate)\(\*\*\{', r'\1(**{"_id": __import__("uuid").uuid4().hex, **{', content)
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Added _id to {f}")
