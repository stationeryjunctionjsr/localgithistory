import os

filepath = 'backend/tests/test_analytics_and_tracking.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix mobile analytics
content = content.replace(
    'event_records = [r for r in all_event_records if r.payload and "testRunId" in r.payload and r.payload["testRunId"] == session_id]',
    'event_records = [r for r in all_event_records if r.payload and getattr(r.payload, "testRunId", None) == session_id]'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
