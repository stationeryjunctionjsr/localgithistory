import os
import re


def update_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Avoid replacing if it's the logger itself or already processed
    if "utils/logger" in filepath or filepath.endswith("logger.ts"):
        return

    if "console.error" in content or "console.warn" in content:
        # Replace occurrences
        new_content = content.replace("console.error", "logger.error").replace("console.warn", "logger.warn")

        # Add import at the top if not present
        if "import { logger } from" not in new_content:
            # Find the last import statement
            imports = [m for m in re.finditer(r"^import .*?;?\n", new_content, re.MULTILINE)]
            if imports:
                last_import = imports[-1]
                insert_pos = last_import.end()
                new_content = (
                    new_content[:insert_pos] + "import { logger } from '@/utils/logger';\n" + new_content[insert_pos:]
                )
            else:
                new_content = "import { logger } from '@/utils/logger';\n" + new_content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")


for root, dirs, files in os.walk("C:/Ecommerce app/frontend/src"):
    for file in files:
        if file.endswith(".ts") or file.endswith(".tsx"):
            update_file(os.path.join(root, file))
