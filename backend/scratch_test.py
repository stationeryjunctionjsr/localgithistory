import re

with open('tests/test_analytics_and_tracking.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('r["type"]', 'r.type')
content = content.replace('r["searchTerm"]', 'r.searchTerm')
content = content.replace('r["resultsCount"]', 'r.resultsCount')
content = content.replace('r["productId"]', 'r.productId')
content = content.replace('r["productName"]', 'r.productName')
content = content.replace('r["source"]', 'r.source')
content = content.replace('r["cartValue"]', 'r.cartValue')
content = content.replace('r["isReturning"]', 'r.isReturning')
content = content.replace('r["page"]', 'r.page')
content = content.replace('r["_id"]', 'r.id')
content = content.replace('ev.id', 'ev.id')

with open('tests/test_analytics_and_tracking.py', 'w', encoding='utf-8') as f:
    f.write(content)
