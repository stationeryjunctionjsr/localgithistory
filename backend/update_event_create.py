import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''class EventCreate(BaseModel):
    eventType: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None''',
'''class EventCreate(BaseModel):
    eventType: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None
    tracking_id: Optional[int] = None'''
)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
