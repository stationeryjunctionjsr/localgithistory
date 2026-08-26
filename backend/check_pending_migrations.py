from sqlalchemy import create_engine, inspect, text

url = "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb"
engine = create_engine(url)
insp = inspect(engine)


def check_indexes():
    print("--- Indexes on sj_products ---")
    indexes = insp.get_indexes("sj_products")
    index_names = [i["name"] for i in indexes]
    print("Found indexes:", index_names)
    expected_indexes = [
        "idx_products_brand",
        "idx_products_category",
        "idx_products_sub_cat",
        "ix_sj_products_lower_brand",
    ]
    for idx in expected_indexes:
        print(f"  Is {idx} present?", idx in index_names)


def check_product_sellers():
    print("\n--- Checking sj_product_sellers (Backfill) ---")
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sj_product_sellers")).scalar()
        print(f"sj_product_sellers row count: {count}")


def check_feature_flags():
    print("\n--- Checking sj_feature_flags ---")
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sj_feature_flags")).scalar()
        print(f"sj_feature_flags row count: {count}")


if __name__ == "__main__":
    check_indexes()
    check_product_sellers()
    check_feature_flags()
