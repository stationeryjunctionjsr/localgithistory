import re

files_to_patch = [
    'frontend/src/app/brands/page.tsx',
    'frontend/src/app/categories/page.tsx',
    'frontend/src/app/customer/page.tsx',
    'frontend/src/app/wholesaler/page.tsx',
    'frontend/src/app/page.tsx'
]

for fp in files_to_patch:
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the broken throw statements
    content = content.replace("throw new Error(API failed with status );", "throw new Error(`API failed with status ${res?.status}`);")
    content = content.replace("logger.error([fetch] network error: );", "logger.error(`[fetch] network error: ${label}`);")
    content = content.replace("throw new Error(Network error: );", "throw new Error(`Network error: ${label}`);")
    content = content.replace("logger.error([fetch] status ${res.status}: );", "logger.error(`[fetch] status ${res.status}: ${label}`);")
    # Actually wait, `logger.error([fetch] status ${res.status}: );` might not match exactly.
    # Let's use regex to fix any `throw new Error(...)` or `logger.error(...)` that lost its backticks.

    # Just fix the ones we see:
    content = re.sub(r'logger\.error\(\[fetch\] status \$\{res\.status\}: \);', r'logger.error(`[fetch] status ${res.status}: ${label}`);', content)
    content = re.sub(r'logger\.error\(\[fetch\] network error: \);', r'logger.error(`[fetch] network error: ${label}`);', content)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)

