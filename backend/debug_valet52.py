import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r"all_active_orders = await order_repository\.findAll\(.*?BUSY_STATUSES.*?\)",
    "all_active_orders = []\n    for st in BUSY_STATUSES:\n        st_orders = await order_repository.findAll({'status': st})\n        all_active_orders.extend([o for o in st_orders if str(o.assigned_valet or '') in available_valet_ids])",
    text
)

text = re.sub(
    r"all_active_returns = await return_request_repository\.findAll\(.*?ACTIVE_RETURN_STATUSES.*?\)",
    "all_active_returns = []\n    for st in ACTIVE_RETURN_STATUSES:\n        st_returns = await return_request_repository.findAll({'status': st})\n        all_active_returns.extend([r for r in st_returns if str(r.assigned_valet or '') in available_valet_ids])",
    text
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
