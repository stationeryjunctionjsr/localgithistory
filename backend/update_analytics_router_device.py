import re
import json

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure json is imported
if 'import json' not in text:
    text = 'import json\n' + text

replacement = '''
    if getattr(event, "device", None):
        val = event.device
        if isinstance(val, dict):
            val = json.dumps(val)
        else:
            val = str(val)
        payload_items.append(EventPayloadItem(key="device", value=val))
'''

text = text.replace(
'''    if getattr(event, "device", None):
        payload_items.append(EventPayloadItem(key="device", value=str(event.device)))''',
replacement)

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)
