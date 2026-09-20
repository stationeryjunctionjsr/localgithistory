import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

valid_columns = [
    'session_id', 'user_id', 'ip_address', 'os', 'browser', 'campaign', 'source',
    'product_id', 'product_name', 'quantity', 'query', 'results_count', 'reason',
    'page', 'screen', 'test_run_id', 'device_type', 'device_os', 'device_os_version',
    'device_model', 'device_app_version'
]

replacement = '''
                # We map keys to columns safely
                col_name = item.key
                if col_name == "ipAddress": col_name = "ip_address"
                elif col_name == "testRunId": col_name = "test_run_id"
                elif col_name == "productId": col_name = "product_id"
                elif col_name == "productName": col_name = "product_name"
                elif col_name == "sessionId": col_name = "session_id"
                elif col_name == "userId": col_name = "user_id"
                elif col_name == "resultsCount": col_name = "results_count"
                
                valid_columns = {
                    "session_id", "user_id", "ip_address", "os", "browser", "campaign", "source",
                    "product_id", "product_name", "quantity", "query", "results_count", "reason",
                    "page", "screen", "test_run_id", "device_type", "device_os", "device_os_version",
                    "device_model", "device_app_version"
                }
                
                # Ensure column is alphanumeric to prevent SQL injection and is a valid column
                if re.match(r'^[a-zA-Z0-9_]+$', col_name) and col_name in valid_columns:
                    cols.append(col_name)
                    vals.append(f":{col_name}")
                    params[col_name] = item.value
'''

text = re.sub(r'                # We map keys to columns safely.*?params\[col_name\] = item\.value', replacement, text, flags=re.DOTALL)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

