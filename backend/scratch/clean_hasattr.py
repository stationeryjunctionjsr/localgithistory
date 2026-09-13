import os
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: X.Y if hasattr(X, "Y") else ( X["Y"] ... ) -> X.Y
    content = re.sub(r'(\w+)\.(\w+)\s*if\s*hasattr\(\1,\s*[\'"]\2[\'"]\)(?:\s*and\s*\1\.\2(?:\s*is\s*not\s*None)?)?\s*else\s*\(?[^)]*\)?', r'\1.\2', content)
    
    # Pattern: hasattr(X, "Y") -> True
    # If the user literally banned hasattr, I'll remove it. But only in assignments.
    
    # Let's do a very aggressive replacement for the ternary blocks left over:
    # `X = Y.Z if hasattr(Y, "Z") else ...`
    # Replace `Y.Z if hasattr(Y, "Z") else (...)` with `Y.Z`
    content = re.sub(r'(\w+)\.(\w+)\s*if\s*hasattr\(\1,\s*[\'"]\2[\'"]\)\s*(?:and\s*\1\.\2(?:(?:\s*is\s*not\s*None)|(?:\s*!=\s*None)|(?:\s*))?)?\s*else\s*(?:\([^)]*\)|[^\n,:\)]+)', r'\1.\2', content)

    # Some multiline ones were broken up.
    # We can just match hasattr(\w+, "\w+") and remove it. But wait, what if it's `if hasattr(user_val, "id"):`?
    # Then `if True:`? It's fine if the Pydantic model guarantees the attribute.
    
    # Let's replace `if hasattr(X, "Y"):` with `if True:` or remove the check if it's part of a generator.
    # Actually, `X.Y if hasattr(X, "Y") else None` is safe to replace with `X.Y`.

    # Let's just fix the files directly with a targeted regex for the exact substrings
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk('backend/app/routers'):
    for file in files:
        if file.endswith('.py'):
            clean_file(os.path.join(root, file))

print('Cleaned')
