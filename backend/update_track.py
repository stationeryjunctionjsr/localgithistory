import re

with open('app/repositories/tracking_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add kwargs to trackSearch
text = re.sub(
    r'    async def trackSearch\(\n        self,\n        user_id: Optional\[str\],\n        search_term: str,\n        results_count: int,\n        session_id: Optional\[str\] = None,\n        product_ids: Optional\[List\[str\]\] = None,\n        segment: str = "customer",\n    \):',
    '    async def trackSearch(\n        self,\n        user_id: Optional[str],\n        search_term: str,\n        results_count: int,\n        session_id: Optional[str] = None,\n        product_ids: Optional[List[str]] = None,\n        segment: str = "customer",\n        os=None, browser=None, ipAddress=None, campaign=None, source=None\n    ):',
    text
)
text = re.sub(
    r'        payload = AnalyticsEventCreate\(\n            type="product_search",\n            userId=user_id,\n            searchTerm=search_term,\n            resultsCount=results_count,\n            sessionId=session_id,\n            segment=segment,\n            productIds=product_ids,\n        \)',
    '        payload = AnalyticsEventCreate(\n            type="product_search",\n            userId=user_id,\n            searchTerm=search_term,\n            resultsCount=results_count,\n            sessionId=session_id,\n            segment=segment,\n            productIds=product_ids,\n            os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source\n        )',
    text
)

with open('app/repositories/tracking_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
