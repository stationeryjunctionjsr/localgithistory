import sys

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old not in content:
            print(f"ERROR: Target string not found!\n{old}")
            sys.exit(1)
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replacements successful.")

replacements = [
    # 1. _row_to_doc
    (
        '"valetDeclineHistory": json_loads(r.valet_decline_history) if getattr(r, "valet_decline_history", None) else [],',
        '"valetDeclineHistory": json_loads(r.valet_decline_history) if getattr(r, "valet_decline_history", None) else [],\n            "isUrgentDelivery": bool(getattr(r, "is_urgent_delivery", False)),'
    ),
    # 2. SELECT queries
    (
        'bill_phone, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, valet_decline_history,',
        'bill_phone, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, valet_decline_history, is_urgent_delivery,'
    ),
    # 3. UPDATE query SET
    (
        'valet_decline_history = :valet_decline_history,\n                        shipped_at = :shipped_at,',
        'valet_decline_history = :valet_decline_history,\n                        is_urgent_delivery = :is_urgent_delivery,\n                        shipped_at = :shipped_at,'
    ),
    # 4. UPDATE query params
    (
        '"valet_decline_history": json_dumps(merged.get("valetDeclineHistory")) if merged.get("valetDeclineHistory") else "[]",',
        '"valet_decline_history": json_dumps(merged.get("valetDeclineHistory")) if merged.get("valetDeclineHistory") else "[]",\n                    "is_urgent_delivery": 1 if merged.get("isUrgentDelivery") else 0,'
    ),
    # 5. CREATE query INSERT
    (
        ':bill_phone, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :valet_decline_history,',
        ':bill_phone, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :valet_decline_history, :is_urgent_delivery,'
    ),
    # 6. CREATE query params
    (
        '"valet_decline_history": json_dumps(data.get("valetDeclineHistory")) if data.get("valetDeclineHistory") else "[]",',
        '"valet_decline_history": json_dumps(data.get("valetDeclineHistory")) if data.get("valetDeclineHistory") else "[]",\n                    "is_urgent_delivery": 1 if data.get("isUrgentDelivery") else 0,'
    )
]

replace_in_file("backend/app/db/mysql_order_dao.py", replacements)
