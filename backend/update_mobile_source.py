import re

with open(r'c:\Ecommerce app\frontend\mobile\src\utils\analytics.ts', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to remove source: 'mobile_app' from getDeviceData so it doesn't pollute everything
# Wait, actually getDeviceData is spread at the root: ...getDeviceData().
# If we remove source, it won't override.

text = text.replace(
'''    campaign: undefined, // Campaign attribution usually handled via deep links in mobile
    source: 'mobile_app',
  };''',
'''    campaign: undefined, // Campaign attribution usually handled via deep links in mobile
  };''')

with open(r'c:\Ecommerce app\frontend\mobile\src\utils\analytics.ts', 'w', encoding='utf-8') as f:
    f.write(text)
