import os
filepath = 'backend/app/db/mysql_flat_daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'await self.db.execute(text(q), params)',
    'factory = self._factory()\n        async with factory() as session:\n            await session.execute(text(q), params)\n            await session.commit()'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
