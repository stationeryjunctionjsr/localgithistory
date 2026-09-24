import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """        for a in saved_addresses:
            if a != address:
                a_params = {'uid': uid, 'st': getattr(a, 'street', None), 'c': getattr(a, 'city', None), 's': getattr(a, 'state', None), 'p': getattr(a, 'pincode', None), 'ph': getattr(a, 'phone', None), 'd': getattr(a, 'district', None), 'co': getattr(a, 'country', None), 'gl': getattr(a, 'googleLocation', None), 'lat': getattr(a, 'latitude', None), 'lon': getattr(a, 'longitude', None), 'at': getattr(a, 'address', None), 'zc': getattr(a, 'zipCode', None)}
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 0, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), a_params)"""

text = text.replace("        for a in saved_addresses:\n            if a != address:\n                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 0, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), {'uid': uid, 'st': a.street, 'c': a.city, 's': a.state, 'p': a.pincode, 'ph': a.phone, 'd': a.district, 'co': a.country, 'gl': a.googleLocation, 'lat': a.latitude, 'lon': a.longitude, 'at': getattr(a, 'address', None), 'zc': getattr(a, 'zipCode', None)})", replacement)

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
