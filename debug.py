import os
with open('backend/app/routers/bundles.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'async def _enrich_bundle' in l:
        with open('out.txt', 'w', encoding='utf-8') as out:
            out.write(''.join(lines[i:i+40]))
        break
