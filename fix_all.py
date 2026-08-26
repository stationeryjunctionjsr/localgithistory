import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Fix any line ending with // some comment} to // some comment\n}
            new_content = re.sub(r'(//[^\n}]*)\}', r'\1\n}', content)

            # Now let's fix the logger.warn ones to use block comments to be 100% safe
            def block_replacer(m):
                comment_text = m.group(1).strip()
                return f'logger.warn("Silent catch block:", e); /* {comment_text} */ }}'

            new_content = re.sub(r'logger\.warn\("Silent catch block:", e\);\s*//([^\n]*)\n\}', block_replacer, new_content)

            # Also fix the import issue in UserEngagementChart and WishlistContext
            new_content = new_content.replace("import {\nimport { logger } from '@/utils/logger';\n", "import { logger } from '@/utils/logger';\nimport {\n")

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed {filepath}")
