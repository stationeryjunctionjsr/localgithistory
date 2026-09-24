import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace _find_next_available_valet_for_return to add prints
text = text.replace('    all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})', '    all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})\n    print(f"DEBUG: all_valets={len(all_valets)}")')
text = text.replace('    eligible_valets = [v for v in all_valets if str(v.id) not in skip_ids]', '    eligible_valets = [v for v in all_valets if str(v.id) not in skip_ids]\n    print(f"DEBUG: eligible_valets={len(eligible_valets)}")')
text = text.replace('    customer_zone_id = str(zone_doc.id) if zone_doc else None', '    customer_zone_id = str(zone_doc.id) if zone_doc else None\n    print(f"DEBUG: customer_zone_id={customer_zone_id}")')
text = text.replace('    avail_map = {str(doc.valet_id): doc for doc in availability_docs if doc.valet_id}', '    avail_map = {str(doc.valet_id): doc for doc in availability_docs if doc.valet_id}\n    print(f"DEBUG: avail_map keys={list(avail_map.keys())}")')
text = text.replace('    if not available_valets:', '    print(f"DEBUG: available_valets={len(available_valets)}")\n    if not available_valets:')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
