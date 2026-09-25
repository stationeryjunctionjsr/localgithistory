import re

filepath = r"app\models\daos.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("class AnalyticsEventCreate(BaseModel):", "class AnalyticsEventCreate(CamelBaseModel):")
text = text.replace("class AnalyticsEventInternalUpdate(BaseModel):", "class AnalyticsEventInternalUpdate(CamelBaseModel):")

for camel, snake in [("ipAddress", "ip_address"), ("testRunId", "test_run_id"), ("sessionId", "session_id"), ("userId", "user_id")]:
    text = re.sub(rf"\b{camel}\b", snake, text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
