# Fix useCoachMarks.ts
fp1 = 'frontend/src/hooks/useCoachMarks.ts'
with open(fp1, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("import { logger } from '@/utils/logger';\n", "")
with open(fp1, 'w', encoding='utf-8') as f:
    f.write(content)

# Fix delivery-slots/page.tsx
fp2 = 'frontend/src/app/admin/delivery-slots/page.tsx'
with open(fp2, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('Applies to "Anytime" delivery', 'Applies to &quot;Anytime&quot; delivery')
with open(fp2, 'w', encoding='utf-8') as f:
    f.write(content)
