import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''async def record_event(
    event: AnalyticsEventCreate = Body(..., description="Analytics event payload"),
    user_info: Optional[User] = Depends(get_optional_user),
):''',
'''async def record_event(
    request: Request,
    event: AnalyticsEventCreate = Body(..., description="Analytics event payload"),
    user_info: Optional[User] = Depends(get_optional_user),
):''')

replacement = '''
    if event.ipAddress:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(event.ipAddress)))
    elif request.client and request.client.host:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(request.client.host)))
'''
text = text.replace('''
    if event.ipAddress:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(event.ipAddress)))''', replacement)

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated app/routers/analytics.py to grab IP from request")
