import os

filepath = 'app/models/daos_flat.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# ActivityInternalCreate
old_create = '''class ActivityInternalCreate(BaseModel):
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    action: str
    comment: Optional[str] = None
    isGuest: Optional[bool] = None
    userAgent: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None'''

new_create = '''class ActivityInternalCreate(CamelBaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str
    comments: Optional[str] = None
    is_guest: Optional[bool] = None
    user_agent: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_type: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None'''

text = text.replace(old_create, new_create)

# ActivityInternalUpdate
old_update = '''class ActivityInternalUpdate(BaseModel):
    userId: Optional[str] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None'''

new_update = '''class ActivityInternalUpdate(CamelBaseModel):
    user_id: Optional[str] = None
    is_guest: Optional[bool] = None
    comments: Optional[str] = None'''

text = text.replace(old_update, new_update)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
