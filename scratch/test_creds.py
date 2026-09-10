import pymysql

credentials = [
    ('root', ''),
    ('root', 'root'),
    ('root', 'Jaimatadi$1607'),
    ('stationeryjunction.jsr', 'Jaimatadi$1607'),
    ('stationeryjunction', 'Jaimatadi$1607'),
    ('stationeryjunction.jsr@gmail.com', 'Jaimatadi$1607')
]

for port in [3306, 13306]:
    print(f"\nTesting port {port}")
    for u, p in credentials:
        try:
            conn = pymysql.connect(host='127.0.0.1', port=port, user=u, password=p)
            print(f"SUCCESS: {u} : {p} on port {port}")
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            print("Databases:", [r[0] for r in cursor.fetchall()])
            conn.close()
        except Exception as e:
            print(f"Failed {u}:{p} => {e}")
