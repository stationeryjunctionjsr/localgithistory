with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if "all_active_orders = await order_repository.findAll({'assignedValet': {'': available_valet_ids}, 'status': {'': BUSY_STATUSES}})" in line:
        out.append("    all_active_orders = []\n")
        out.append("    for st in BUSY_STATUSES:\n")
        out.append("        st_orders = await order_repository.findAll({'status': st})\n")
        out.append("        all_active_orders.extend([o for o in st_orders if str(o.assigned_valet or '') in available_valet_ids])\n")
        continue
    
    if "all_active_returns = await return_request_repository.findAll({'status': {'': ACTIVE_RETURN_STATUSES}})" in line:
        out.append("    all_active_returns = []\n")
        out.append("    for st in ACTIVE_RETURN_STATUSES:\n")
        out.append("        st_returns = await return_request_repository.findAll({'status': st})\n")
        out.append("        all_active_returns.extend([r for r in st_returns if str(r.assigned_valet or '') in available_valet_ids])\n")
        continue
        
    out.append(line)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
print("SUCCESS")
