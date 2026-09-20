import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
    payload_items.append(EventPayloadItem(key="userId", value=str(user_id) if user_id else ""))
    payload_items.append(EventPayloadItem(key="sessionId", value=str(event.sessionId) if event.sessionId else ""))
    payload_items.append(EventPayloadItem(key="timestamp", value=str(event.timestamp) if event.timestamp else datetime.now(timezone.utc).isoformat()))
    if event.os:
        payload_items.append(EventPayloadItem(key="os", value=str(event.os)))
    if event.browser:
        payload_items.append(EventPayloadItem(key="browser", value=str(event.browser)))
    if event.campaign:
        payload_items.append(EventPayloadItem(key="campaign", value=str(event.campaign)))
    if event.ipAddress:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(event.ipAddress)))
    if getattr(event, "device", None):
        payload_items.append(EventPayloadItem(key="device", value=str(event.device)))
'''

text = text.replace(
'''    payload_items.append(EventPayloadItem(key="userId", value=str(user_id) if user_id else ""))
    payload_items.append(EventPayloadItem(key="sessionId", value=str(event.sessionId) if event.sessionId else ""))
    payload_items.append(EventPayloadItem(key="timestamp", value=str(event.timestamp) if event.timestamp else datetime.now(timezone.utc).isoformat()))''',
replacement)

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated app/routers/analytics.py")
