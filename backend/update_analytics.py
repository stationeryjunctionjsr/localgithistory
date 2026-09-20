import re

with open(r'c:\Ecommerce app\frontend\src\utils\analytics.ts', 'r', encoding='utf-8') as f:
    text = f.read()

helper_code = '''
export const getDeviceData = () => {
  if (typeof window === 'undefined') return {};
  
  const ua = navigator.userAgent;
  let os = 'Unknown';
  if (ua.indexOf('Win') !== -1) os = 'Windows';
  else if (ua.indexOf('Mac') !== -1) os = 'MacOS';
  else if (ua.indexOf('X11') !== -1) os = 'UNIX';
  else if (ua.indexOf('Linux') !== -1) os = 'Linux';
  else if (ua.indexOf('Android') !== -1) os = 'Android';
  else if (ua.indexOf('like Mac') !== -1) os = 'iOS';

  let browser = 'Unknown';
  if (ua.indexOf('Chrome') !== -1) browser = 'Chrome';
  else if (ua.indexOf('Safari') !== -1) browser = 'Safari';
  else if (ua.indexOf('Firefox') !== -1) browser = 'Firefox';
  else if (ua.indexOf('Edge') !== -1) browser = 'Edge';

  const params = new URLSearchParams(window.location.search);
  const campaign = params.get('utm_campaign') || undefined;
  const utmSource = params.get('utm_source') || undefined;

  return {
    os,
    browser,
    campaign,
    ...(utmSource && { source: utmSource }),
  };
};
'''

text = text.replace('export const getSessionId = () => {', helper_code + '\nexport const getSessionId = () => {')

def replace_post(call_str):
    # e.g. api.post('/tracking/cart-add', { productId, quantity, sessionId: getSessionId(), });
    # we want to insert ...getDeviceData(), inside the object.
    pass

# We will just do a simple string replace for each tracking method.
for method in ['cart-add', 'cart-remove', 'view', 'filter-click', 'error', 'session', 'search']:
    text = text.replace(f"api.post('/tracking/{method}', {{", f"api.post('/tracking/{method}', {{\n      ...getDeviceData(),")

text = text.replace(f"api.post('/tracking/click', {{\n      productId,", f"api.post('/tracking/click', {{\n      ...getDeviceData(),\n      productId,")


with open(r'c:\Ecommerce app\frontend\src\utils\analytics.ts', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated web analytics.ts")
