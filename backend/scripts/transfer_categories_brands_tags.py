import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

load_dotenv()
if not os.environ.get("DATABASE_URL"):
    print("Set DATABASE_URL in .env and run again.")
    sys.exit(1)


async def load_json(collection: str) -> list:
    path = backend_root / "app" / "data" / f"{collection}.json"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text or "[]")
    except json.JSONDecodeError:
        return []


def safe_timestamp(ts):
    try:
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except:
        pass
    return datetime.utcnow()


async def clear_table(session, table_name: str):
    from sqlalchemy import text

    try:
        await session.execute(text(f"DELETE FROM {table_name}"))
        await session.commit()
        print(f"Cleared table {table_name}")
    except Exception as e:
        await session.rollback()
        print(f"Failed to clear {table_name}: {e}")


async def migrate_categories():
    from sqlalchemy import text
    from app.config.database import get_async_session_factory

    factory = get_async_session_factory()
    if not factory:
        return 0
    docs = await load_json("categories")
    count = 0
    async with factory() as session:
        await clear_table(session, "sj_categories")
        for doc in docs:
            eid = doc.get("_id") or doc.get("id")
            if not eid:
                continue
            images = json.dumps(doc.get("images", []), default=str)
            sub_categories = json.dumps(doc.get("subCategories", []), default=str)
            category_tags = json.dumps(doc.get("categoryTags", []), default=str)
            created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
            updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
            try:
                await session.execute(
                    text("""
                        INSERT INTO sj_categories (
                            external_id, name, description, images, sub_categories, is_active,
                            category_tag, category_tags, minimum_quantity, show_in_mobile_homepage,
                            gst, is_returnable,
                            created_at, updated_at
                        ) VALUES (
                            :eid, :name, :description, :images, :sub_categories, :is_active,
                            :category_tag, :category_tags, :min_qty, :show_mobile,
                            :gst, :is_returnable,
                            :created, :updated
                        )
                    """),
                    {
                        "eid": str(eid),
                        "name": doc.get("name"),
                        "description": doc.get("description"),
                        "images": images,
                        "sub_categories": sub_categories,
                        "is_active": 1 if doc.get("isActive", True) else 0,
                        "category_tag": doc.get("categoryTag"),
                        "category_tags": category_tags,
                        "min_qty": doc.get("minimumQuantity", 0),
                        "show_mobile": 1 if doc.get("showInMobileHomepage", True) else 0,
                        "gst": float(doc.get("gst", 0.0)),
                        "is_returnable": 1 if doc.get("isReturnable", False) else 0,
                        "created": created,
                        "updated": updated,
                    },
                )
                count += 1
            except Exception as e:
                print(f"Failed category {eid}: {e}")
        await session.commit()
    return count


async def migrate_brands():
    from sqlalchemy import text
    from app.config.database import get_async_session_factory

    factory = get_async_session_factory()
    if not factory:
        return 0
    docs = await load_json("brands")
    count = 0
    async with factory() as session:
        await clear_table(session, "sj_brands")
        for doc in docs:
            eid = doc.get("_id") or doc.get("id")
            if not eid:
                continue
            created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
            updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
            try:
                await session.execute(
                    text("""
                        INSERT INTO sj_brands (
                            external_id, name, slug, image_url, is_active, created_at, updated_at
                        ) VALUES (
                            :eid, :name, :slug, :image_url, :is_active, :created, :updated
                        )
                    """),
                    {
                        "eid": str(eid),
                        "name": doc.get("name"),
                        "slug": doc.get("slug"),
                        "image_url": doc.get("imageUrl") or doc.get("image_url"),
                        "is_active": 1 if doc.get("isActive", True) else 0,
                        "created": created,
                        "updated": updated,
                    },
                )
                count += 1
            except Exception as e:
                print(f"Failed brand {eid}: {e}")
        await session.commit()
    return count


async def migrate_category_tags():
    from sqlalchemy import text
    from app.config.database import get_async_session_factory

    factory = get_async_session_factory()
    if not factory:
        return 0
    docs = await load_json("categoryTags")
    count = 0
    async with factory() as session:
        await clear_table(session, "sj_category_tags")
        for doc in docs:
            eid = doc.get("_id") or doc.get("id")
            if not eid:
                continue
            created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
            updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
            try:
                await session.execute(
                    text("""
                        INSERT INTO sj_category_tags (
                            external_id, name, description, is_active, created_at, updated_at
                        ) VALUES (
                            :eid, :name, :description, :is_active, :created, :updated
                        )
                    """),
                    {
                        "eid": str(eid),
                        "name": doc.get("name"),
                        "description": doc.get("description"),
                        "is_active": 1 if doc.get("isActive", True) else 0,
                        "created": created,
                        "updated": updated,
                    },
                )
                count += 1
            except Exception as e:
                print(f"Failed category tag {eid}: {e}")
        await session.commit()
    return count


async def main():
    print("Migrating Category Tags...")
    count_ct = await migrate_category_tags()
    print(f"Migrated {count_ct} category tags.")

    print("Migrating Categories...")
    count_c = await migrate_categories()
    print(f"Migrated {count_c} categories.")

    print("Migrating Brands...")
    count_b = await migrate_brands()
    print(f"Migrated {count_b} brands.")


if __name__ == "__main__":
    asyncio.run(main())
