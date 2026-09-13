import pymysql

drop_sqls = [
    "ALTER TABLE `sj_orders` DROP COLUMN `valet_decline_history`;",
    "ALTER TABLE `sj_return_requests` DROP COLUMN `valet_decline_history`;",
    "ALTER TABLE `sj_coupons` DROP COLUMN `seller_ids`;",
    "ALTER TABLE `sj_coupons` DROP COLUMN `cart_items`;",
    "ALTER TABLE `sj_coupons` DROP COLUMN `extra_data`;"
]

for db in ['sjqadb', 'sjuatdb']:
    try:
        conn = pymysql.connect(host='127.0.0.1', port=13306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607', database=db)
        cursor = conn.cursor()
        for sql in drop_sqls:
            try:
                cursor.execute(sql)
                print(f"[{db}] Executed: {sql}")
            except Exception as e:
                pass # Column might already be dropped or table doesn't exist
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error connecting to {db}: {e}")
