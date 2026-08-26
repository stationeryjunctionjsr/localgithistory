import re

with open("backend/app/db/mysql_order_dao.py", "r", encoding="utf-8") as f:
    c = f.read()

# Replace row_to_doc
c = re.sub(
    r'"shippingAddress": json_loads\(r\.shipping_address\) or \{\},\s*"billingAddress": json_loads\(r\.billing_address\) or \{\},',
    """"shippingAddress": {
                "name": r.ship_name,
                "phone": r.ship_phone,
                "street": r.ship_street,
                "city": r.ship_city,
                "state": r.ship_state,
                "pincode": r.ship_pincode,
            },
            "billingAddress": {
                "name": r.bill_name,
                "phone": r.bill_phone,
                "street": r.bill_street,
                "city": r.bill_city,
                "state": r.bill_state,
                "pincode": r.bill_pincode,
            },""",
    c,
)

# Replace SELECT queries
c = re.sub(
    r"shipping_address,\s*billing_address,",
    "ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone,",
    c,
)

# Replace INSERT and UPDATE SQL
c = re.sub(
    r"shipping_address, billing_address,",
    "ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone,",
    c,
)

c = re.sub(
    r":shipping_address, :billing_address,",
    ":ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone,",
    c,
)

c = re.sub(
    r"shipping_address\s*=\s*:shipping_address,",
    "ship_name = :ship_name, ship_street = :ship_street, ship_city = :ship_city, ship_state = :ship_state, ship_pincode = :ship_pincode, ship_phone = :ship_phone,",
    c,
)
c = re.sub(
    r"billing_address\s*=\s*:billing_address,",
    "bill_name = :bill_name, bill_street = :bill_street, bill_city = :bill_city, bill_state = :bill_state, bill_pincode = :bill_pincode, bill_phone = :bill_phone,",
    c,
)

# Replace params in create()
c = re.sub(
    r'"shipping_address": json_dumps\(data\.get\("shippingAddress"\) or \{\}\),',
    """"ship_name": (data.get("shippingAddress") or {}).get("name"),
                    "ship_street": (data.get("shippingAddress") or {}).get("street"),
                    "ship_city": (data.get("shippingAddress") or {}).get("city"),
                    "ship_state": (data.get("shippingAddress") or {}).get("state"),
                    "ship_pincode": (data.get("shippingAddress") or {}).get("pincode"),
                    "ship_phone": (data.get("shippingAddress") or {}).get("phone"),""",
    c,
)

c = re.sub(
    r'"billing_address": json_dumps\(data\.get\("billingAddress"\) or \{\}\),',
    """"bill_name": (data.get("billingAddress") or {}).get("name"),
                    "bill_street": (data.get("billingAddress") or {}).get("street"),
                    "bill_city": (data.get("billingAddress") or {}).get("city"),
                    "bill_state": (data.get("billingAddress") or {}).get("state"),
                    "bill_pincode": (data.get("billingAddress") or {}).get("pincode"),
                    "bill_phone": (data.get("billingAddress") or {}).get("phone"),""",
    c,
)

# Replace params in update()
c = re.sub(
    r'"shipping_address": json_dumps\(merged\.get\("shippingAddress"\) or \{\}\),',
    """"ship_name": (merged.get("shippingAddress") or {}).get("name"),
                    "ship_street": (merged.get("shippingAddress") or {}).get("street"),
                    "ship_city": (merged.get("shippingAddress") or {}).get("city"),
                    "ship_state": (merged.get("shippingAddress") or {}).get("state"),
                    "ship_pincode": (merged.get("shippingAddress") or {}).get("pincode"),
                    "ship_phone": (merged.get("shippingAddress") or {}).get("phone"),""",
    c,
)

c = re.sub(
    r'"billing_address": json_dumps\(merged\.get\("billingAddress"\) or \{\}\),',
    """"bill_name": (merged.get("billingAddress") or {}).get("name"),
                    "bill_street": (merged.get("billingAddress") or {}).get("street"),
                    "bill_city": (merged.get("billingAddress") or {}).get("city"),
                    "bill_state": (merged.get("billingAddress") or {}).get("state"),
                    "bill_pincode": (merged.get("billingAddress") or {}).get("pincode"),
                    "bill_phone": (merged.get("billingAddress") or {}).get("phone"),""",
    c,
)

with open("backend/app/db/mysql_order_dao.py", "w", encoding="utf-8") as f:
    f.write(c)
