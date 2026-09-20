import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update findAll SQL
text = text.replace(
    'text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC")',
    'text(f"SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type FROM {self.TABLE} e LEFT JOIN sj_tracking t ON e.tracking_id = t.id WHERE {where_sql.replace(\'event_type\', \'e.event_type\')} ORDER BY e.id ASC")'
)

# Update findById SQL
text = text.replace(
    'text(f"SELECT * FROM {self.TABLE} WHERE id = :id")',
    'text(f"SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type FROM {self.TABLE} e LEFT JOIN sj_tracking t ON e.tracking_id = t.id WHERE e.id = :id")'
)

# Update valid_columns mapped arrays
new_valid_columns = '''
        # Unmap flat columns back to payload
        valid_columns = {
            "session_id": "sessionId", "user_id": "userId", "ip_address": "ipAddress", 
            "os": "os", "browser": "browser", "campaign": "campaign", "source": "source",
            "product_id": "productId", "product_name": "productName", "quantity": "quantity", 
            "query": "query", "results_count": "resultsCount", "reason": "reason",
            "page": "page", "screen": "screen", "test_run_id": "testRunId", 
            "device_type": "device_type", 
            "device_os_version": "device_os_version", "device_model": "device_model", 
            "device_app_version": "device_app_version"
        }
'''

text = re.sub(
    r'        # Unmap flat columns back to payload\n        valid_columns = {.*?        }',
    new_valid_columns.strip('\n'),
    text,
    flags=re.DOTALL
)

# Update create valid columns
new_create_valid = '''
                valid_columns = {
                    "product_id", "product_name", "quantity", "query", "results_count", "reason",
                    "page", "screen", "test_run_id", "device_os_version",
                    "device_model", "device_app_version"
                }
'''
text = re.sub(
    r'                valid_columns = {.*?                }',
    new_create_valid.strip('\n'),
    text,
    flags=re.DOTALL
)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated mysql_events_dao.py")
