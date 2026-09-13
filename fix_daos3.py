import re
with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = re.sub(r'merged = \w+InternalUpdate\(\**\{\**existing\.model_dump\(by_alias=True\), \**data\.model_dump\(exclude_unset=True\)\}\)', 'merged = {**existing.model_dump(by_alias=True), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)}', c)
c = re.sub(r'if hasattr\(merged, "([\"]+)"\) and getattr\(merged, "([\"]+)"\) is not None:', r(if "\g<1>" in merged and merged["\g<1>"] is not None:', c)
c = re.sub(r'merged\.([\w]+)', r'merged["\g<1>"]', c)
with open('backend/app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")