import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# I need to fix the _fetch_children method or the way it constructs the EventResponse.
# The EventResponse needs to map flat columns to payload items, or just not fetch children!

replacement = '''    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        # We no longer have a child table. Return empty.
        c_map = {rid: {"payload": []} for rid in ids}
        return c_map
'''

text = re.sub(r'    async def _fetch_children\(self, session, ids: List\[int\]\) -> Dict\[int, Dict\]:.*?(?=    def _row_to_event)', replacement, text, flags=re.DOTALL)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

