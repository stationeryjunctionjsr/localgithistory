with open('app/db/mysql_order_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Update SELECTs
text = text.replace('ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone', 'ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude')

text = text.replace(':ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone', ':ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :ship_address, :ship_district, :ship_country, :ship_google_location, :ship_latitude, :ship_longitude, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :bill_address, :bill_district, :bill_country, :bill_google_location, :bill_latitude, :bill_longitude')

text = text.replace('ship_name = :ship_name, ship_street = :ship_street, ship_city = :ship_city, ship_state = :ship_state, ship_pincode = :ship_pincode, ship_phone = :ship_phone,\n                        bill_name = :bill_name, bill_street = :bill_street, bill_city = :bill_city, bill_state = :bill_state, bill_pincode = :bill_pincode, bill_phone = :bill_phone,', 'ship_name = :ship_name, ship_street = :ship_street, ship_city = :ship_city, ship_state = :ship_state, ship_pincode = :ship_pincode, ship_phone = :ship_phone, ship_address = :ship_address, ship_district = :ship_district, ship_country = :ship_country, ship_google_location = :ship_google_location, ship_latitude = :ship_latitude, ship_longitude = :ship_longitude,\n                        bill_name = :bill_name, bill_street = :bill_street, bill_city = :bill_city, bill_state = :bill_state, bill_pincode = :bill_pincode, bill_phone = :bill_phone, bill_address = :bill_address, bill_district = :bill_district, bill_country = :bill_country, bill_google_location = :bill_google_location, bill_latitude = :bill_latitude, bill_longitude = :bill_longitude,')

# Update __map_to_schema
old_map = '''            "shippingAddress": {
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
            },'''

new_map = '''            "shippingAddress": {
                "name": r.ship_name,
                "phone": r.ship_phone,
                "street": r.ship_street,
                "city": r.ship_city,
                "state": r.ship_state,
                "pincode": r.ship_pincode,
                "address": getattr(r, "ship_address", None),
                "district": getattr(r, "ship_district", None),
                "country": getattr(r, "ship_country", None),
                "googleLocation": getattr(r, "ship_google_location", None),
                "latitude": getattr(r, "ship_latitude", None),
                "longitude": getattr(r, "ship_longitude", None),
            },
            "billingAddress": {
                "name": r.bill_name,
                "phone": r.bill_phone,
                "street": r.bill_street,
                "city": r.bill_city,
                "state": r.bill_state,
                "pincode": r.bill_pincode,
                "address": getattr(r, "bill_address", None),
                "district": getattr(r, "bill_district", None),
                "country": getattr(r, "bill_country", None),
                "googleLocation": getattr(r, "bill_google_location", None),
                "latitude": getattr(r, "bill_latitude", None),
                "longitude": getattr(r, "bill_longitude", None),
            },'''
text = text.replace(old_map, new_map)

# Update _prepare_params create
old_create_params = '''                    "ship_city":    data.shippingAddress.city    if data.shippingAddress else None,
                    "ship_state":   data.shippingAddress.state   if data.shippingAddress else None,
                    "ship_pincode": data.shippingAddress.pincode if data.shippingAddress else None,
                    "ship_phone":   data.shippingAddress.phone   if data.shippingAddress else None,
                    "bill_name":    data.billingAddress.name     if data.billingAddress else None,
                    "bill_street":  data.billingAddress.street   if data.billingAddress else None,
                    "bill_city":    data.billingAddress.city     if data.billingAddress else None,
                    "bill_state":   data.billingAddress.state    if data.billingAddress else None,
                    "bill_pincode": data.billingAddress.pincode  if data.billingAddress else None,
                    "bill_phone":   data.billingAddress.phone    if data.billingAddress else None,'''

new_create_params = '''                    "ship_city":    data.shippingAddress.city    if data.shippingAddress else None,
                    "ship_state":   data.shippingAddress.state   if data.shippingAddress else None,
                    "ship_pincode": data.shippingAddress.pincode if data.shippingAddress else None,
                    "ship_phone":   data.shippingAddress.phone   if data.shippingAddress else None,
                    "ship_address": data.shippingAddress.address if data.shippingAddress else None,
                    "ship_district": data.shippingAddress.district if data.shippingAddress else None,
                    "ship_country": data.shippingAddress.country if data.shippingAddress else None,
                    "ship_google_location": data.shippingAddress.googleLocation if data.shippingAddress else None,
                    "ship_latitude": data.shippingAddress.latitude if data.shippingAddress else None,
                    "ship_longitude": data.shippingAddress.longitude if data.shippingAddress else None,
                    "bill_name":    data.billingAddress.name     if data.billingAddress else None,
                    "bill_street":  data.billingAddress.street   if data.billingAddress else None,
                    "bill_city":    data.billingAddress.city     if data.billingAddress else None,
                    "bill_state":   data.billingAddress.state    if data.billingAddress else None,
                    "bill_pincode": data.billingAddress.pincode  if data.billingAddress else None,
                    "bill_phone":   data.billingAddress.phone    if data.billingAddress else None,
                    "bill_address": data.billingAddress.address if data.billingAddress else None,
                    "bill_district": data.billingAddress.district if data.billingAddress else None,
                    "bill_country": data.billingAddress.country if data.billingAddress else None,
                    "bill_google_location": data.billingAddress.googleLocation if data.billingAddress else None,
                    "bill_latitude": data.billingAddress.latitude if data.billingAddress else None,
                    "bill_longitude": data.billingAddress.longitude if data.billingAddress else None,'''
text = text.replace(old_create_params, new_create_params)

# Update _prepare_params update
old_update_params = '''                    "ship_city": (update_data.shippingAddress.city if update_data.shippingAddress else (existing.shipping_address.city if existing.shipping_address else None)),
                    "ship_state": (update_data.shippingAddress.state if update_data.shippingAddress else (existing.shipping_address.state if existing.shipping_address else None)),
                    "ship_pincode": (update_data.shippingAddress.pincode if update_data.shippingAddress else (existing.shipping_address.pincode if existing.shipping_address else None)),
                    "ship_phone": (update_data.shippingAddress.phone if update_data.shippingAddress else (existing.shipping_address.phone if existing.shipping_address else None)),
                    "bill_name": (update_data.billingAddress.name if update_data.billingAddress else (existing.billing_address.name if existing.billing_address else None)),
                    "bill_street": (update_data.billingAddress.street if update_data.billingAddress else (existing.billing_address.street if existing.billing_address else None)),
                    "bill_city": (update_data.billingAddress.city if update_data.billingAddress else (existing.billing_address.city if existing.billing_address else None)),
                    "bill_state": (update_data.billingAddress.state if update_data.billingAddress else (existing.billing_address.state if existing.billing_address else None)),
                    "bill_pincode": (update_data.billingAddress.pincode if update_data.billingAddress else (existing.billing_address.pincode if existing.billing_address else None)),
                    "bill_phone": (update_data.billingAddress.phone if update_data.billingAddress else (existing.billing_address.phone if existing.billing_address else None)),'''

new_update_params = '''                    "ship_city": (update_data.shippingAddress.city if update_data.shippingAddress else (existing.shipping_address.city if existing.shipping_address else None)),
                    "ship_state": (update_data.shippingAddress.state if update_data.shippingAddress else (existing.shipping_address.state if existing.shipping_address else None)),
                    "ship_pincode": (update_data.shippingAddress.pincode if update_data.shippingAddress else (existing.shipping_address.pincode if existing.shipping_address else None)),
                    "ship_phone": (update_data.shippingAddress.phone if update_data.shippingAddress else (existing.shipping_address.phone if existing.shipping_address else None)),
                    "ship_address": (update_data.shippingAddress.address if update_data.shippingAddress else (getattr(existing.shipping_address, "address", None) if existing.shipping_address else None)),
                    "ship_district": (update_data.shippingAddress.district if update_data.shippingAddress else (getattr(existing.shipping_address, "district", None) if existing.shipping_address else None)),
                    "ship_country": (update_data.shippingAddress.country if update_data.shippingAddress else (getattr(existing.shipping_address, "country", None) if existing.shipping_address else None)),
                    "ship_google_location": (update_data.shippingAddress.googleLocation if update_data.shippingAddress else (getattr(existing.shipping_address, "googleLocation", None) if existing.shipping_address else None)),
                    "ship_latitude": (update_data.shippingAddress.latitude if update_data.shippingAddress else (getattr(existing.shipping_address, "latitude", None) if existing.shipping_address else None)),
                    "ship_longitude": (update_data.shippingAddress.longitude if update_data.shippingAddress else (getattr(existing.shipping_address, "longitude", None) if existing.shipping_address else None)),
                    "bill_name": (update_data.billingAddress.name if update_data.billingAddress else (existing.billing_address.name if existing.billing_address else None)),
                    "bill_street": (update_data.billingAddress.street if update_data.billingAddress else (existing.billing_address.street if existing.billing_address else None)),
                    "bill_city": (update_data.billingAddress.city if update_data.billingAddress else (existing.billing_address.city if existing.billing_address else None)),
                    "bill_state": (update_data.billingAddress.state if update_data.billingAddress else (existing.billing_address.state if existing.billing_address else None)),
                    "bill_pincode": (update_data.billingAddress.pincode if update_data.billingAddress else (existing.billing_address.pincode if existing.billing_address else None)),
                    "bill_phone": (update_data.billingAddress.phone if update_data.billingAddress else (existing.billing_address.phone if existing.billing_address else None)),
                    "bill_address": (update_data.billingAddress.address if update_data.billingAddress else (getattr(existing.billing_address, "address", None) if existing.billing_address else None)),
                    "bill_district": (update_data.billingAddress.district if update_data.billingAddress else (getattr(existing.billing_address, "district", None) if existing.billing_address else None)),
                    "bill_country": (update_data.billingAddress.country if update_data.billingAddress else (getattr(existing.billing_address, "country", None) if existing.billing_address else None)),
                    "bill_google_location": (update_data.billingAddress.googleLocation if update_data.billingAddress else (getattr(existing.billing_address, "googleLocation", None) if existing.billing_address else None)),
                    "bill_latitude": (update_data.billingAddress.latitude if update_data.billingAddress else (getattr(existing.billing_address, "latitude", None) if existing.billing_address else None)),
                    "bill_longitude": (update_data.billingAddress.longitude if update_data.billingAddress else (getattr(existing.billing_address, "longitude", None) if existing.billing_address else None)),'''
text = text.replace(old_update_params, new_update_params)

with open('app/db/mysql_order_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
