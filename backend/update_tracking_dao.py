import re

with open('app/db/mysql_tracking_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
        add_col("campaign", "campaign", data.campaign)
        add_col("deviceType", "device_type", getattr(data, "deviceType", None))
        add_col("deviceOsVersion", "device_os_version", getattr(data, "deviceOsVersion", None))
        add_col("deviceModel", "device_model", getattr(data, "deviceModel", None))
        add_col("deviceAppVersion", "device_app_version", getattr(data, "deviceAppVersion", None))
'''

text = re.sub(
    r'        add_col\("campaign", "campaign", data\.campaign\)',
    replacement.strip('\n'),
    text
)

with open('app/db/mysql_tracking_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
