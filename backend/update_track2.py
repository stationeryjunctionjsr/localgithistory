import re

with open('app/repositories/tracking_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace signatures
text = re.sub(
    r', os=None, browser=None, ipAddress=None, campaign=None, source=None',
    ', **kwargs',
    text
)

# Replace AnalyticsEventCreate calls
text = re.sub(
    r'os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, ',
    '**kwargs, ',
    text
)

# Wait, trackSearch was manually modified in the previous step to have os=os, ...
# Let's verify trackSearch
text = re.sub(
    r'os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source',
    '**kwargs',
    text
)

with open('app/repositories/tracking_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
