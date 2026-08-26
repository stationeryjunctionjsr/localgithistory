import re

with open("backend/app/db/mysql_user_dao.py", "r", encoding="utf-8") as f:
    c = f.read()

# Replace row_to_doc
c = re.sub(
    r"address\s*=\s*parse_json.*?saved_addresses\s*=\s*parse_json.*?seller_permissions\s*=\s*parse_json.*?service_area_zones\s*=\s*parse_json.*?\n",
    "",
    c,
    flags=re.DOTALL,
)

c = re.sub(
    r'"address": address or \{\},\s*"savedAddresses": saved_addresses or \[\],\s*"isActive": bool\(r\.is_active\)',
    """"address": children.get("address", {}),
            "savedAddresses": children.get("savedAddresses", []),
            "isActive": bool(r.is_active)""",
    c,
)

c = re.sub(
    r'"sellerPermissions": seller_permissions or \{\},\s*"serviceAreaZones": service_area_zones or \[\],',
    """"sellerPermissions": children.get("sellerPermissions", {}),
            "serviceAreaZones": children.get("serviceAreaZones", []),""",
    c,
)

# In findAll/find_paginated, we need to pass children_map
c = re.sub(r"def _row_to_doc\(self, r\)", "def _row_to_doc(self, r, children)", c)

# Need to update SELECT columns in all 5 places
select_pattern = r"role,\s*phone,\s*company_name,\s*address,\s*saved_addresses,\s*is_active,.*?is_seller_admin,\s*seller_permissions,\s*service_area_zones,\s*is_on_duty,\s*commission_override_pct,"
new_select = "role, phone, company_name, is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms, assigned_salesperson, is_email_verified, referral_code, is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,"
c = re.sub(select_pattern, new_select, c, flags=re.DOTALL)

# Handle INSERT and UPDATE
c = re.sub(
    r"role,\s*phone,\s*company_name,\s*address,\s*saved_addresses,\s*is_active,.*?is_seller_admin,\s*seller_permissions,\s*service_area_zones,\s*is_on_duty,\s*commission_override_pct,",
    "role, phone, company_name, is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms, assigned_salesperson, is_email_verified, referral_code, is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,",
    c,
    flags=re.DOTALL,
)
c = re.sub(
    r":role,\s*:phone,\s*:company_name,\s*:address,\s*:saved_addresses,\s*:is_active,.*?:is_seller_admin,\s*:seller_permissions,\s*:service_area_zones,\s*:is_on_duty,\s*:commission_override_pct,",
    ":role, :phone, :company_name, :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms, :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin, :allow_delivery_slots, :allow_urgent_delivery, :is_on_duty, :commission_override_pct,",
    c,
    flags=re.DOTALL,
)
c = re.sub(r"address\s*=\s*:address,\s*saved_addresses\s*=\s*:saved_addresses,", "", c)
c = re.sub(
    r"seller_permissions\s*=\s*:seller_permissions,\s*service_area_zones\s*=\s*:service_area_zones,",
    "allow_delivery_slots = :allow_delivery_slots, allow_urgent_delivery = :allow_urgent_delivery,",
    c,
)

# Replace params assignment in create/update
c = re.sub(r'"address": address_json,.*?saved_json,', "", c, flags=re.DOTALL)
c = re.sub(
    r'"seller_permissions": seller_perms_json,',
    '"allow_delivery_slots": 1 if data.get("sellerPermissions", {}).get("allowDeliverySlots") else 0, "allow_urgent_delivery": 1 if data.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,',
    c,
    count=1,
)
c = re.sub(
    r'"seller_permissions": seller_perms_json,',
    '"allow_delivery_slots": 1 if merged.get("sellerPermissions", {}).get("allowDeliverySlots") else 0, "allow_urgent_delivery": 1 if merged.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,',
    c,
)
c = re.sub(r'"service_area_zones": service_zones_json,', "", c)

# We will inject a massive block for _fetch_children and _replace_children.
# Actually, since it's tricky to inject with regex, I'll write a Python script that builds the new DAO entirely, like I did for Products.
