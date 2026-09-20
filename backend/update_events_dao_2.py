import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update findAll SQL
text = text.replace(
    'SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type FROM {self.TABLE} e',
    'SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type, t.device_os_version, t.device_model, t.device_app_version FROM {self.TABLE} e'
)

# Update create valid columns
new_create_valid = '''
                valid_columns = {
                    "product_id", "product_name", "quantity", "query", "results_count", "reason",
                    "page", "screen", "test_run_id"
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
