import os
import re


def fix_empty_catches():
    count = 0
    for root, _, files in os.walk('frontend/src'):
        for file in files:
            if not file.endswith('.ts') and not file.endswith('.tsx'):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix empty promise catches: .catch(() => {}) or .catch((e) => {})
            promise_catch_pattern = r'\.catch\(\s*\([^)]*\)\s*=>\s*\{\s*\}\s*\)'
            content = re.sub(promise_catch_pattern, '.catch((e) => logger.warn("Promise rejected silently:", e))', content)

            # Fix empty try-catch blocks (with optional comments inside)
            # Regex explanation:
            # catch               : literally 'catch'
            # \s*                 : optional whitespace
            # (\([^)]+\))?        : optional '(e)' or '(err: any)'
            # \s*                 : optional whitespace
            # \{                  : opening brace
            # (?:[ \t\r\n]|//.*)* : any mix of whitespace and single-line comments
            # \}                  : closing brace

            def replacer(match):
                # We need to preserve the comments if any
                inner = match.group(0)
                # Extract comments
                comments = " ".join(re.findall(r'//.*', inner))
                return f'catch (e) {{ logger.warn("Silent catch block:", e); {comments} }}'

            catch_pattern = r'catch\s*(\([^)]+\))?\s*\{((?:[ \t\r\n]|//.*)*)\}'
            content = re.sub(catch_pattern, replacer, content)

            if content != original_content:
                # Add logger import if missing
                if 'import { logger } from' not in content:
                    imports = [m for m in re.finditer(r'^import .*?;?\n', content, re.MULTILINE)]
                    if imports:
                        last_import = imports[-1]
                        insert_pos = last_import.end()
                        content = content[:insert_pos] + "import { logger } from '@/utils/logger';\n" + content[insert_pos:]
                    else:
                        content = "import { logger } from '@/utils/logger';\n" + content

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1
                print(f"Patched {filepath}")

    print(f"Total files patched: {count}")

fix_empty_catches()
