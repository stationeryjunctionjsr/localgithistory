import os
import re

filepath = 'app/models/daos_flat.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Make ActivityInternal inherit from CamelBaseModel
text = text.replace('class ActivityInternal(BaseModel):', 'from app.models.base import CamelBaseModel\nclass ActivityInternal(CamelBaseModel):')

# Convert camelCase fields to snake_case in ActivityInternal
act_internal_old = '''    id: str = Field(alias="_id")
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    action: str
    comment: Optional[str] = None
    isGuest: Optional[bool] = None
    userAgent: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None'''

act_internal_new = '''    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str
    comments: Optional[str] = None
    is_guest: Optional[bool] = None
    user_agent: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None'''

text = text.replace(act_internal_old, act_internal_new)

# Note: The database column is 'comments' instead of 'comment'. I used 'comments' above.

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
