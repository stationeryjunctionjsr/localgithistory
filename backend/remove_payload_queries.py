import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace findAll child loading
text = re.sub(
    r'child_rows = \(\s*await session\.execute\(\s*text\(f"SELECT parent_id, payload_key, payload_value FROM sj_event_payload WHERE parent_id IN \(\{id_placeholders\}\)"\),\s*id_params\s*\)\s*\)\.fetchall\(\)\s*payload_map = \{pid: \[\] for pid in ids\}\s*for cr in child_rows:\s*payload_map\[cr\.parent_id\]\.append\(EventPayloadItem\(key=cr\.payload_key, value=cr\.payload_value\)\)',
    'payload_map = {pid: [] for pid in ids}',
    text,
    flags=re.DOTALL
)

# Replace findById child loading
text = re.sub(
    r'child_rows = \(\s*await session\.execute\(\s*text\("SELECT payload_key, payload_value FROM sj_event_payload WHERE parent_id = :id"\),\s*\{"id": pid\}\s*\)\s*\)\.fetchall\(\)\s*payload = \[EventPayloadItem\(key=r\.payload_key, value=r\.payload_value\) for r in child_rows\]',
    'payload = []',
    text,
    flags=re.DOTALL
)

# Replace update child saving
text = re.sub(
    r'if data\.payload is not None:\s*await session\.execute\(\s*text\("DELETE FROM sj_event_payload WHERE parent_id = :pid"\),\s*\{"pid": pid\}\s*\)\s*for item in data\.payload:\s*await session\.execute\(\s*text\("INSERT INTO sj_event_payload \(parent_id, payload_key, payload_value\) VALUES \(:pid, :k, :v\)"\),\s*\{"pid": pid, "k": item\.key, "v": item\.value\}\s*\)',
    '',
    text,
    flags=re.DOTALL
)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

