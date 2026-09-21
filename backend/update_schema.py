with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_schema = '''class TicketResponseItemInternal(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user: Optional[str] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    createdAt: Optional[str] = None'''

new_schema = '''class TicketResponseItemInternal(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user: Optional[str] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    createdAt: Optional[str] = None
    isAdminResponse: Optional[bool] = None'''

if old_schema in text:
    text = text.replace(old_schema, new_schema)
else:
    print("Could not find TicketResponseItemInternal in schemas.py")

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
