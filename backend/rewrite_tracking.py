import re

with open('app/repositories/tracking_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('get_storage("tracking")', 'get_storage("events")')

if 'EventCreate' not in text:
    text = text.replace(
        'from app.models.schemas import AnalyticsEventCreate',
        'from app.models.schemas import AnalyticsEventCreate\nfrom app.db.mysql_events_dao import EventCreate, EventPayloadItem'
    )

wrapper = '''
    async def create(self, tracking_data: AnalyticsEventCreate):
        if tracking_data.timestamp is None:
            tracking_data.timestamp = self._get_current_timestamp()

        payload = []
        for k, v in tracking_data.model_dump(by_alias=True, exclude_none=True).items():
            if k not in ('type', 'userId', 'sessionId', 'timestamp') and v is not None:
                if isinstance(v, list):
                    payload.append(EventPayloadItem(key=k, value=str(v)))
                else:
                    payload.append(EventPayloadItem(key=k, value=str(v)))
        if tracking_data.user_id:
            payload.append(EventPayloadItem(key='userId', value=str(tracking_data.user_id)))
        if tracking_data.session_id:
            payload.append(EventPayloadItem(key='sessionId', value=str(tracking_data.session_id)))
        if tracking_data.timestamp:
            payload.append(EventPayloadItem(key='timestamp', value=str(tracking_data.timestamp)))

        event_create = EventCreate(
            event_type=tracking_data.type,
            payload=payload
        )
        return await self.storage.create(event_create)

    def _extract(self, event, key, snake_key=None):
        if hasattr(event, snake_key or key) and getattr(event, snake_key or key) is not None:
            return getattr(event, snake_key or key)
        if hasattr(event, 'payload') and event.payload:
            for p in event.payload:
                if p.key == key:
                    return p.value
        return None
'''

text = re.sub(
    r'\s*async def create\(self, tracking_data: AnalyticsEventCreate\):.*?return datetime\.now\(timezone\.utc\)\.isoformat\(\)',
    wrapper + '\n    def _get_current_timestamp(self):\n        return datetime.now(timezone.utc).isoformat()',
    text,
    flags=re.DOTALL
)

# Now replace aggregations in tracking_repository to use _extract
text = re.sub(r's\.timestamp', 'self._extract(s, "timestamp")', text)
text = re.sub(r'v\.timestamp', 'self._extract(v, "timestamp")', text)
text = re.sub(r'd\.timestamp', 'self._extract(d, "timestamp")', text)
text = re.sub(r'a\.timestamp', 'self._extract(a, "timestamp")', text)

text = re.sub(r'v\.product_id', 'self._extract(v, "productId", "product_id")', text)
text = re.sub(r'v\.product_name', 'self._extract(v, "productName", "product_name")', text)

text = re.sub(r'd\.page', 'self._extract(d, "page")', text)
text = re.sub(r'd\.reason', 'self._extract(d, "reason")', text)

text = re.sub(r'a\.cart_items', 'self._extract(a, "cartItems", "cart_items")', text)
text = re.sub(r'a\.cart_value', 'self._extract(a, "cartValue", "cart_value")', text)

# For getRecentUserSearches
text = re.sub(r's\.search_term', 'self._extract(s, "searchTerm", "search_term")', text)

# For getReturningUsers
text = re.sub(r'u\.is_returning', 'self._extract(u, "isReturning", "is_returning")', text)
text = re.sub(r'u\.user_id', 'self._extract(u, "userId", "user_id")', text)
text = re.sub(r'u\.timestamp', 'self._extract(u, "timestamp")', text)

# Replace findAll({"type": ...}) with findAll({"event_type": ...}) because events table uses event_type
text = re.sub(r'findAll\(\{"type"', r'findAll({"event_type"', text)

with open('app/repositories/tracking_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
