import asyncio
import pymysql

def main():
    # URL is mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb
    conn = pymysql.connect(
        host='127.0.0.1',
        port=13306,
        user='stationeryjunction.jsr@gmail.com',
        password='Jaimatadi$1607',
        database='sjqadb',
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        try:
            cur.execute("ALTER TABLE sj_delivery_slots ADD COLUMN zone_id VARCHAR(255) DEFAULT 'default';")
            print("Added zone_id column")
        except Exception as e:
            print(e)
            
        cur.execute("DESCRIBE sj_delivery_slots")
        print([r["Field"] for r in cur.fetchall()])
    conn.commit()

if __name__ == "__main__":
    main()
