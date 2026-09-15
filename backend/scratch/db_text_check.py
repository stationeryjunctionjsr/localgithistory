import sqlalchemy
from sqlalchemy import create_engine, text

db_url = 'mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi%241607@127.0.0.1:13306/sjqadb'

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Checking sj_product_details...")
        res = conn.execute(text("SELECT detail_value FROM sj_product_details LIMIT 5;")).fetchall()
        print(res)
        
        print("Checking sj_tracking_payload...")
        res2 = conn.execute(text("SELECT payload_value FROM sj_tracking_payload LIMIT 5;")).fetchall()
        print(res2)
except Exception as e:
    print(f"Error: {e}")
