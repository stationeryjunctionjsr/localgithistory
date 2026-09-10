import pymysql

try:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607')
    cursor = conn.cursor()
    cursor.execute('SHOW DATABASES')
    print("Databases on 3306:")
    for row in cursor.fetchall():
        print(row[0])
    conn.close()
except Exception as e:
    print(f"Error on 3306: {e}")

try:
    conn = pymysql.connect(host='127.0.0.1', port=13306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607')
    cursor = conn.cursor()
    cursor.execute('SHOW DATABASES')
    print("\nDatabases on 13306:")
    for row in cursor.fetchall():
        print(row[0])
    conn.close()
except Exception as e:
    print(f"Error on 13306: {e}")
