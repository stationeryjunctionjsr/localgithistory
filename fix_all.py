import json
import re

def update_mysql_order_dao():
    path = 'backend/app/db/mysql_order_dao.py'
    with open(path, 'r') as f:
        content = f.read()

    # Add columns to SELECT
    content = content.replace(
        'printed_bill, assigned_valet,',
        'printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, valet_decline_history,'
    )

    # Add columns to INSERT
    content = content.replace(
        'printed_bill, assigned_valet,\\n',
        'printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, valet_decline_history,\\n'
    )
    content = content.replace(
        ':printed_bill, :assigned_valet,\\n',
        ':printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :valet_decline_history,\\n'
    )

    # Add columns to UPDATE
    content = content.replace(
        'assigned_valet = :assigned_valet,\\n',
        'assigned_valet = :assigned_valet,\\n                        pending_valet_id = :pending_valet_id,\\n                        valet_assigned_at = :valet_assigned_at,\\n                        valet_cascade_count = :valet_cascade_count,\\n                        valet_decline_history = :valet_decline_history,\\n'
    )

    # Add to _row_to_doc
    row_to_doc_insert = '''            "assignedValet": r.assigned_valet,
            "pendingValetId": getattr(r, "pending_valet_id", None),
            "valetAssignedAt": r.valet_assigned_at.isoformat() + "Z" if getattr(r, "valet_assigned_at", None) else None,
            "valetCascadeCount": getattr(r, "valet_cascade_count", 0),
            "valetDeclineHistory": json_loads(r.valet_decline_history) if getattr(r, "valet_decline_history", None) else [],'''
    content = content.replace('"assignedValet": r.assigned_valet,', row_to_doc_insert)

    # Add to create params
    create_params_insert = '''                    "assigned_valet": data.get("assignedValet"),
                    "pending_valet_id": data.get("pendingValetId"),
                    "valet_assigned_at": _to_ts(data.get("valetAssignedAt")),
                    "valet_cascade_count": data.get("valetCascadeCount") or 0,
                    "valet_decline_history": json_dumps(data.get("valetDeclineHistory")) if data.get("valetDeclineHistory") else "[]",'''
    content = content.replace('"assigned_valet": data.get("assignedValet"),', create_params_insert, 1)

    # Add to update params
    update_params_insert = '''                    "assigned_valet": merged.get("assignedValet"),
                    "pending_valet_id": merged.get("pendingValetId"),
                    "valet_assigned_at": _to_ts(merged.get("valetAssignedAt")),
                    "valet_cascade_count": merged.get("valetCascadeCount") or 0,
                    "valet_decline_history": json_dumps(merged.get("valetDeclineHistory")) if merged.get("valetDeclineHistory") else "[]",'''
    
    # We replaced the first one, now replace the second one (which is for update)
    if update_params_insert.split('\n')[0] not in content[content.find('def update'):]:
        parts = content.split('def update')
        parts[1] = parts[1].replace('"assigned_valet": merged.get("assignedValet"),', update_params_insert)
        content = 'def update'.join(parts)

    with open(path, 'w') as f:
        f.write(content)
    print("Updated mysql_order_dao.py")


def update_schema_mysql():
    path = 'backend/scripts/schema_mysql.sql'
    with open(path, 'r') as f:
        content = f.read()

    new_cols = '''  ssigned_valet varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  pending_valet_id varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  alet_assigned_at datetime DEFAULT NULL,
  alet_cascade_count int DEFAULT '0',
  alet_decline_history longtext COLLATE utf8mb4_unicode_ci,'''
    
    content = content.replace('  ssigned_valet varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,', new_cols)
    
    with open(path, 'w') as f:
        f.write(content)
    print("Updated schema_mysql.sql")


def update_routers_returns():
    path = 'backend/app/routers/returns.py'
    with open(path, 'r') as f:
        content = f.read()

    old_logic = '''        history = list(ret.get("valetDeclineHistory") or [])
        valet_id_str = str(current_user.get("_id"))
        if valet_id_str not in history:
            history.append(valet_id_str)'''
    
    new_logic = '''        history = list(ret.get("valetDeclineHistory") or [])
        valet_id_str = str(current_user.get("_id"))
        if not any(isinstance(d, dict) and d.get("valetId") == valet_id_str for d in history):
            history.append({"valetId": valet_id_str, "reason": response_data.declineReason})'''
    
    content = content.replace(old_logic, new_logic)
    
    with open(path, 'w') as f:
        f.write(content)
    print("Updated routers/returns.py")


def update_valet_timeout_job():
    path = 'backend/app/jobs/valet_timeout_job.py'
    with open(path, 'r') as f:
        content = f.read()

    old_logic1 = '''                    if pending_valet_id:
                        history = list(order.get("valetDeclineHistory") or [])
                        if pending_valet_id not in history:
                            history.append(pending_valet_id)
                        order["valetDeclineHistory"] = history'''
    
    new_logic1 = '''                    if pending_valet_id:
                        history = list(order.get("valetDeclineHistory") or [])
                        if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
                            history.append({"valetId": pending_valet_id, "reason": "timeout"})
                        order["valetDeclineHistory"] = history'''
    content = content.replace(old_logic1, new_logic1)

    old_logic2 = '''                    if pending_valet_id:
                        history = list(ret.get("valetDeclineHistory") or [])
                        if pending_valet_id not in history:
                            history.append(pending_valet_id)
                        ret["valetDeclineHistory"] = history'''
    
    new_logic2 = '''                    if pending_valet_id:
                        history = list(ret.get("valetDeclineHistory") or [])
                        if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
                            history.append({"valetId": pending_valet_id, "reason": "timeout"})
                        ret["valetDeclineHistory"] = history'''
    content = content.replace(old_logic2, new_logic2)

    with open(path, 'w') as f:
        f.write(content)
    print("Updated valet_timeout_job.py")


def update_schemas():
    path = 'backend/app/models/schemas.py'
    with open(path, 'r') as f:
        content = f.read()

    content = content.replace(
        '    valet: Optional[Dict[str, Any]] = None  # populated valet\n    valetDeclineHistory: Optional[List[str]] = None',
        '    valet: Optional[Dict[str, Any]] = None  # populated valet\n    pendingValetId: Optional[str] = None\n    valetDeclineHistory: Optional[List[Dict[str, Any]]] = None'
    )
    with open(path, 'w') as f:
        f.write(content)
    print("Updated schemas.py")


def update_typed_doc_configs():
    path = 'backend/app/db/typed_doc_configs.py'
    with open(path, 'r') as f:
        content = f.read()

    # Add deliverySlotConfigId
    content = content.replace(
        '"deliverySlotId": "delivery_slot_id",',
        '"deliverySlotId": "delivery_slot_id",\\n            "deliverySlotConfigId": "delivery_slot_config_id",'
    )
    # Remove valetDeclineHistory from clob_map
    content = content.replace(
        '{"items": "items", "valetDeclineHistory": "valet_decline_history"},',
        '{"items": "items"},'
    )
    with open(path, 'w') as f:
        f.write(content)
    print("Updated typed_doc_configs.py")


def update_frontend_valet_page():
    path = 'frontend/src/app/valet/page.tsx'
    with open(path, 'r') as f:
        content = f.read()

    # The duplicated blocks are like:
    # {req.deliverySlot && ( ... )}
    # There are multiple of them. Let's find the large block where it's duplicated.
    # A regex might be safer.
    
    # We want to replace all occurrences of:
    block = '''                            {req.deliverySlot && (
                              <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-100 shadow-sm flex flex-col">
                                <span className="text-xs text-purple-800 font-semibold uppercase tracking-wider mb-1">
                                  ?? Scheduled Pickup Slot
                                </span>
                                <span className="text-sm text-purple-900 font-medium">
                                  {req.deliverySlot.startTime} - {req.deliverySlot.endTime}
                                  {req.deliverySlot.date &&  ()}
                                </span>
                              </div>
                            )}'''
    
    count = content.count(block)
    print(f"Found {count} duplicated blocks in valet/page.tsx")
    
    if count > 1:
        # Keep exactly 1
        content = content.replace(block, "<!--DEL-->")
        content = content.replace("<!--DEL-->", block, 1)
        content = content.replace("<!--DEL-->", "")
    
    with open(path, 'w') as f:
        f.write(content)
    print("Updated valet/page.tsx")

def update_mobile_valet():
    path = 'frontend/mobile/app/valet/index.tsx'
    with open(path, 'r') as f:
        content = f.read()

    content = content.replace(
        "api.put(/returns//valet-response",
        "api.put(/returns/valet//response"
    )
    with open(path, 'w') as f:
        f.write(content)
    print("Updated mobile/app/valet/index.tsx")

def update_admin_returns_page():
    path = 'frontend/src/app/admin/returns-management/page.tsx'
    with open(path, 'r') as f:
        content = f.read()
    
    content = content.replace(
        "<div>Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime}</div>",
        "<div>Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime}{ret.deliverySlot.date &&  ()}</div>"
    )
    with open(path, 'w') as f:
        f.write(content)
    print("Updated admin returns page")

update_mysql_order_dao()
update_schema_mysql()
update_routers_returns()
update_valet_timeout_job()
update_schemas()
update_typed_doc_configs()
update_frontend_valet_page()
update_mobile_valet()
update_admin_returns_page()
