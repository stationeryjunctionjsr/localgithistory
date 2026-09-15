import sqlalchemy
from sqlalchemy import create_engine, text

# Need to escape the % in the connection string if passed directly, or just use it as is since it's url encoded
db_url = 'mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi%241607@127.0.0.1:13306/sjqadb'

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'sjqadb' AND DATA_TYPE IN ('json');"))
        json_cols = result.fetchall()
        
        print("JSON Columns Found:")
        if json_cols:
            for row in json_cols:
                print(f"Table: {row[0]}, Column: {row[1]}, Type: {row[2]}")
        else:
            print("No JSON columns found.")
            
        print("\nChecking for potential text blobs that might hold JSON...")
        result_text = conn.execute(text("SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'sjqadb' AND DATA_TYPE IN ('longtext', 'mediumtext', 'text');"))
        text_cols = result_text.fetchall()
        for row in text_cols:
            print(f"Table: {row[0]}, Column: {row[1]}, Type: {row[2]}")
            
except Exception as e:
    print(f"Error: {e}")
