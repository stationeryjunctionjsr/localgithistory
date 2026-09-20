import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove 'if event.payload.device is not None:' code block (2 lines)
text = re.sub(
    r'        if event\.payload\.device is not None:\n            payload_items\.append\(EventPayloadItem\(key="device", value=str\(event\.payload\.device\)\)\)\n',
    '',
    text
)

# And if there is any duplicated OS logic, let's just make sure we only capture OS once if it's identical
# Or just ensure device_os and os are handled.

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)
