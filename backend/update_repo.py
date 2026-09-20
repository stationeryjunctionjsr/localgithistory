import re

with open('app/repositories/tracking_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update trackSession
text = re.sub(
    r'    async def trackSession\(self, user_id: Optional\[str\], session_id: str, is_returning: bool, os=None, browser=None, ipAddress=None, campaign=None, source=None\):.*?pageViews=1\n            \)\n        \)',
    '    async def trackSession(self, user_id: Optional[str], session_id: str, is_returning: bool, os=None, browser=None, ipAddress=None, campaign=None, source=None, deviceType=None, deviceOsVersion=None, deviceModel=None, deviceAppVersion=None):\n        return await self.create(\n            AnalyticsEventCreate(\n                type="session", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, \n                userId=user_id, sessionId=session_id, isReturning=is_returning, pageViews=1, deviceType=deviceType, deviceOsVersion=deviceOsVersion, deviceModel=deviceModel, deviceAppVersion=deviceAppVersion\n            )\n        )',
    text,
    flags=re.DOTALL
)

# And similarly for all other methods... actually this is a lot of methods.
# Wait, I can just use a global regex if they all look similar, or just rewrite them.
