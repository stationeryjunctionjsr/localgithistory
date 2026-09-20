import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Define the mapping
mapping_code = '''
        # Unmap flat columns back to payload
        valid_columns = {
            "session_id": "sessionId", "user_id": "userId", "ip_address": "ipAddress", 
            "os": "os", "browser": "browser", "campaign": "campaign", "source": "source",
            "product_id": "productId", "product_name": "productName", "quantity": "quantity", 
            "query": "query", "results_count": "resultsCount", "reason": "reason",
            "page": "page", "screen": "screen", "test_run_id": "testRunId", 
            "device_type": "device_type", "device_os": "device_os", 
            "device_os_version": "device_os_version", "device_model": "device_model", 
            "device_app_version": "device_app_version"
        }
'''

# Update findAll
find_all_replacement = '''
            result.append(EventResponse(
                id=str(r.id),
                externalId=r.external_id,
                eventType=r.event_type,
                payload=[EventPayloadItem(key=k_camel, value=str(getattr(r, k_db))) for k_db, k_camel in valid_columns.items() if hasattr(r, k_db) and getattr(r, k_db) is not None],
                createdAt=r.created_at,
                updatedAt=r.updated_at
            ))
'''
# Note: findAll previously had:
#         result = []
#         for r in rows:
#             result.append(EventResponse(
#                 id=str(r.id),
#                 externalId=r.external_id,
#                 eventType=r.event_type,
#                 payload=(payload_map[r.id] if r.id in payload_map else []),
#                 createdAt=r.created_at,
#                 updatedAt=r.updated_at
#             ))
text = re.sub(
    r'        result = \[\]\n        for r in rows:\n            result\.append\(EventResponse\(\n                id=str\(r\.id\),\n                externalId=r\.external_id,\n                eventType=r\.event_type,\n                payload=.*?,\n                createdAt=r\.created_at,\n                updatedAt=r\.updated_at\n            \)\)',
    mapping_code + '\n        result = []\n        for r in rows:' + find_all_replacement,
    text,
    flags=re.DOTALL
)


# Update findById
# Note: findById previously had:
#         payload_list = []
#             
#         return EventResponse(
#             id=str(row.id),
#             externalId=row.external_id,
#             eventType=row.event_type,
#             payload=payload_list,
#             createdAt=row.created_at,
#             updatedAt=row.updated_at
#         )
find_by_id_replacement = mapping_code + '''
        payload_list = [EventPayloadItem(key=k_camel, value=str(getattr(row, k_db))) for k_db, k_camel in valid_columns.items() if hasattr(row, k_db) and getattr(row, k_db) is not None]
            
        return EventResponse(
            id=str(row.id),
            externalId=row.external_id,
            eventType=row.event_type,
            payload=payload_list,
            createdAt=row.created_at,
            updatedAt=row.updated_at
        )
'''

text = re.sub(
    r'        payload_list = \[\]\n            \n        return EventResponse\(\n            id=str\(row\.id\),\n            externalId=row\.external_id,\n            eventType=row\.event_type,\n            payload=payload_list,\n            createdAt=row\.created_at,\n            updatedAt=row\.updated_at\n        \)',
    find_by_id_replacement,
    text,
    flags=re.DOTALL
)


with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

