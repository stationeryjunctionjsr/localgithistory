
files = [
  "frontend/src/components/SessionAnalytics.tsx",
  "frontend/src/context/AuthContext.tsx",
  "frontend/src/context/CartContext.tsx",
  "frontend/src/store/cartStore.ts",
  "frontend/src/utils/analytics.ts"
]

for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'import { logger }' not in content:
        content = "import { logger } from '@/utils/logger';\n" + content
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added logger to {fp}")
