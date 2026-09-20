import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
        # Unify OS
        final_os = event.os
        final_browser = event.browser
        final_device_type = None
        final_device_os_version = None
        final_device_model = None
        final_device_app_version = None

        if getattr(event, "device", None) and isinstance(event.device, dict):
            if not final_os and event.device.get("os"):
                final_os = event.device.get("os")
            if not final_browser and event.device.get("browser"):
                final_browser = event.device.get("browser")
            
            final_device_type = event.device.get("type")
            final_device_os_version = event.device.get("osVersion")
            final_device_model = event.device.get("model")
            final_device_app_version = event.device.get("appVersion")

        # Determine IP Address
        final_ip = event.ipAddress
        if not final_ip and request.client and request.client.host:
            final_ip = request.client.host

        final_campaign = event.campaign
        final_source = event.source

        kwargs = {
            "os": final_os,
            "browser": final_browser,
            "ipAddress": final_ip,
            "campaign": final_campaign,
            "source": final_source,
            "deviceType": final_device_type,
            "deviceOsVersion": final_device_os_version,
            "deviceModel": final_device_model,
            "deviceAppVersion": final_device_app_version
        }
'''

text = re.sub(
    r'        # Unify OS.*?        kwargs = \{.*?        \}',
    replacement.strip('\n'),
    text,
    flags=re.DOTALL
)

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated analytics.py")
