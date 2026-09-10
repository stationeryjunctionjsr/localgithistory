import asyncio, json
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    f = get_async_session_factory()
    async with f() as s:
        checks = [
            ("sj_orders",          "valet_decline_history", "id"),
            ("sj_return_requests", "valet_decline_history", "id"),
            ("sj_delivery_zones",  "seller_ids",            "id"),
            ("sj_coupons",         "extra_data",            "id"),
            ("sj_tracking",        "cart_items",            "id"),
        ]
        for table, col, pk in checks:
            r = await s.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != 'null'"))
            cnt = r.scalar()
            r2 = await s.execute(text(f"SELECT {pk}, {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != 'null' LIMIT 2"))
            samples = r2.fetchall()
            print(f"\n=== {table}.{col}: {cnt} non-empty rows ===")
            for row in samples:
                val = row[1]
                try:
                    parsed = json.loads(val) if val else None
                    print(f"  id={row[0]}: {json.dumps(parsed)[:200]}")
                except Exception:
                    print(f"  id={row[0]}: (raw) {str(val)[:200]}")

asyncio.run(main())
