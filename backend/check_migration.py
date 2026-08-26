from sqlalchemy import create_engine, inspect

url = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb"
engine = create_engine(url)
insp = inspect(engine)

try:
    cols = [c["name"] for c in insp.get_columns("sj_seller_availability")]
    print("sj_seller_availability columns:")
    print(cols)
    print("\nIs 'reason' in sj_seller_availability?", "reason" in cols)

    so_cols = [c["name"] for c in insp.get_columns("sj_sub_orders")]
    print("\nIs 'sub_order_number' in sj_sub_orders?", "sub_order_number" in so_cols)

except Exception as e:
    print("Error:", e)
