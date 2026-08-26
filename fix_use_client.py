fp = 'frontend/src/context/AuthContext.tsx'
with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("import { logger } from '@/utils/logger';\n\ufeff'use client';", "\ufeff'use client';\nimport { logger } from '@/utils/logger';")

with open(fp, 'w', encoding='utf-8') as f:
    f.write(content)
