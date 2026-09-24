import re

with open('app/repositories/notification_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('if notification_data.createdAt is None:', 'if getattr(notification_data, "createdAt", notification_data.get("createdAt") if isinstance(notification_data, dict) else None) is None:\n            if isinstance(notification_data, dict):\n                notification_data["createdAt"] = self._get_timestamp()\n            else:\n                notification_data.createdAt = self._get_timestamp()\n        if False:')

text = text.replace('if notification_data.updatedAt is None:', 'if getattr(notification_data, "updatedAt", notification_data.get("updatedAt") if isinstance(notification_data, dict) else None) is None:\n            if isinstance(notification_data, dict):\n                notification_data["updatedAt"] = self._get_timestamp()\n            else:\n                notification_data.updatedAt = self._get_timestamp()\n        if False:')

with open('app/repositories/notification_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
