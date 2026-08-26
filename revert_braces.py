import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Reverse the bad brace fix
            new_content = re.sub(r'(//[^}\n]*)\n\}', r'\1}', content)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Reverted braces in {filepath}")
