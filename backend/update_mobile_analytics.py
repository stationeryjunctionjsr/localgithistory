import re

with open(r'c:\Ecommerce app\frontend\mobile\src\utils\analytics.ts', 'r', encoding='utf-8') as f:
    text = f.read()

# Add a getDeviceData function to mobile as well, but tailored to React Native!

helper_code = '''
const getDeviceData = () => {
  return {
    os: Device.osName || Platform.OS,
    browser: 'MobileApp',
    campaign: undefined, // Campaign attribution usually handled via deep links in mobile
    source: 'mobile_app',
  };
};
'''

text = text.replace('const buildDevice = () => {', helper_code + '\nconst buildDevice = () => {')

text = text.replace('      device: event.device || buildDevice(),', '      device: event.device || buildDevice(),\n      ...getDeviceData(),')

with open(r'c:\Ecommerce app\frontend\mobile\src\utils\analytics.ts', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated mobile analytics.ts")
