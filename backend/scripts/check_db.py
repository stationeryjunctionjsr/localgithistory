import asyncio
import os
import pymysql


def main():
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "13306"))
    user = os.environ.get("DB_USER", "")
    password = os.environ.get("DB_PASSWORD", "")
    database = os.environ.get("DB_NAME", "sjqadb")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
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
