import re

filepath = r"app\db\mysql_sub_order_dao.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the giant _map_to_schema block
replacement = '''    def _map_to_schema(self, row, items_rows=None) -> 'SubOrder':
        d = dict(row._mapping)
        d["id"] = str(d["id"])
        
        # Flattened nested objects
        d["delivery_slot"] = None
        if d.get("delivery_slot_config_id") or d.get("delivery_slot_id") or d.get("delivery_slot_date"):
            d["delivery_slot"] = {
                "configId": d.get("delivery_slot_config_id"),
                "slotId": d.get("delivery_slot_id"),
                "date": d.get("delivery_slot_date"),
            }

        d["coupon_info"] = None
        if d.get("coupon_info_type") or d.get("coupon_info_value") is not None:
            d["coupon_info"] = {
                "discountType": d.get("coupon_info_type"),
                "discountValue": float(d.get("coupon_info_value")) if d.get("coupon_info_value") is not None else 0,
            }

        d["shipping_address"] = {
            "name": d.get("shipping_name"),
            "phone": d.get("shipping_phone"),
            "street": d.get("shipping_line1"),
            "city": d.get("shipping_city"),
            "state": d.get("shipping_state"),
            "pincode": d.get("shipping_pincode"),
        }

        d["billing_address"] = {
            "name": d.get("billing_name"),
            "phone": d.get("billing_phone"),
            "street": d.get("billing_line1"),
            "city": d.get("billing_city"),
            "state": d.get("billing_state"),
            "pincode": d.get("billing_pincode"),
        }

        items = []
        if items_rows:
            for it in items_rows:
                if getattr(it, "sub_order_id", None) == row.id:
                    items.append({
                        "productId": it.product_id, 
                        "name": it.name, 
                        "qty": it.qty, 
                        "price": float(it.price)
                    })
        d["items"] = items

        from app.models.sub_order import SubOrder
        return SubOrder.model_validate(d)'''

# regex replace
text = re.sub(r'    def _map_to_schema\(self, row, items_rows=None\) -> \'SubOrder\':.*?return SubOrder\(\*\*doc\)', replacement, text, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
