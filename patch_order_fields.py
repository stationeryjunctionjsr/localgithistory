import os
filepath = 'backend/app/repositories/order_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '        fields = {}\n        for f in update_data.model_fields_set:',
    '        if isinstance(update_data, dict):\n            return await self.storage.update(id, update_data)\n        fields = {}\n        for f in getattr(update_data, "model_fields_set", []):'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
