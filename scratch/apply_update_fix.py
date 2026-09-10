import sys

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old not in content:
            print(f"ERROR: Target string not found!\n\nTarget:\n{old}")
            sys.exit(1)
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replacements successful.")

replacements = [
    # 1. UPDATE SET
    (
        'assigned_valet = :assigned_valet,\n                        shipped_at = :shipped_at,',
        'assigned_valet = :assigned_valet,\n                        pending_valet_id = :pending_valet_id,\n                        valet_assigned_at = :valet_assigned_at,\n                        valet_cascade_count = :valet_cascade_count,\n                        valet_decline_history = :valet_decline_history,\n                        is_urgent_delivery = :is_urgent_delivery,\n                        shipped_at = :shipped_at,'
    ),
    # 2. UPDATE params
    (
        '"assigned_valet": merged.get("assignedValet"),\n                    "shipped_at": _to_ts(merged.get("shippedAt")),',
        '"assigned_valet": merged.get("assignedValet"),\n                    "pending_valet_id": merged.get("pendingValetId"),\n                    "valet_assigned_at": _to_ts(merged.get("valetAssignedAt")),\n                    "valet_cascade_count": merged.get("valetCascadeCount") or 0,\n                    "valet_decline_history": json_dumps(merged.get("valetDeclineHistory")) if merged.get("valetDeclineHistory") else "[]",\n                    "is_urgent_delivery": 1 if merged.get("isUrgentDelivery") else 0,\n                    "shipped_at": _to_ts(merged.get("shippedAt")),'
    ),
    # 3. CREATE params
    (
        '"assigned_valet": data.get("assignedValet"),\n                    "pending_valet_id": data.get("pendingValetId"),',
        '"assigned_valet": data.get("assignedValet"),\n                    "is_urgent_delivery": 1 if data.get("isUrgentDelivery") else 0,\n                    "pending_valet_id": data.get("pendingValetId"),'
    )
]

replace_in_file("backend/app/db/mysql_order_dao.py", replacements)
