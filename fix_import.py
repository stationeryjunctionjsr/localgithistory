for path in ['frontend/src/app/customer/page.tsx', 'frontend/src/app/wholesaler/page.tsx']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'import { logger }' not in content:
        content = "import { logger } from '@/utils/logger';\n" + content
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
