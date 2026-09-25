import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """        if address:
            params = {'uid': uid, 'st': getattr(address, 'street', None), 'c': getattr(address, 'city', None), 's': getattr(address, 'state', None), 'p': getattr(address, 'pincode', None), 'ph': getattr(address, 'phone', None), 'd': getattr(address, 'district', None), 'co': getattr(address, 'country', None), 'gl': getattr(address, 'googleLocation', None), 'lat': getattr(address, 'latitude', None), 'lon': getattr(address, 'longitude', None), 'at': getattr(address, 'address', None), 'zc': getattr(address, 'zipCode', None)}
            try:
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 1, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), params)
            except Exception as e:
                import traceback
                print("CRASH ON ADDRESS PARAMS:", params)
                traceback.print_exc()
                raise e"""

text = text.replace("        if address:\n            await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 1, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), {'uid': uid, 'st': address.street, 'c': address.city, 's': address.state, 'p': address.pincode, 'ph': address.phone, 'd': address.district, 'co': address.country, 'gl': address.google_location, 'lat': address.latitude, 'lon': address.longitude, 'at': address.address, 'zc': getattr(address, 'zipCode', None)})", replacement)

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
