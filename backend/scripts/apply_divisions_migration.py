"""
Migration script to introduce sj_divisions, sj_division_category_tags,
and division_id on sj_category_tags.
Migrates any data from sj_category_heads seamlessly.
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run_migration():
    factory = get_async_session_factory()
    if not factory:
        print("Database not configured.")
        return

    async with factory() as session:
        print("Creating sj_divisions table...")
        await session.execute(text('''
            CREATE TABLE IF NOT EXISTS sj_divisions (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                external_id VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL UNIQUE,
                description VARCHAR(4000) DEFAULT NULL,
                image_url VARCHAR(1000) DEFAULT NULL,
                display_order INT NOT NULL DEFAULT 0,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT NULL,
                updated_at DATETIME DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        '''))

        # Check if sj_category_heads has data to migrate into sj_divisions
        tables_res = await session.execute(text("SHOW TABLES LIKE 'sj_category_heads'"))
        if tables_res.fetchone():
            print("Migrating records from sj_category_heads to sj_divisions...")
            await session.execute(text('''
                INSERT INTO sj_divisions (id, external_id, name, description, image_url, display_order, is_active, created_at, updated_at)
                SELECT id, external_id, name, description, image_url, display_order, is_active, created_at, updated_at
                FROM sj_category_heads
                ON DUPLICATE KEY UPDATE 
                    name = VALUES(name),
                    description = VALUES(description),
                    display_order = VALUES(display_order),
                    is_active = VALUES(is_active);
            '''))

        # Add division_id column to sj_category_tags
        cols_res = await session.execute(text("DESCRIBE sj_category_tags"))
        cols = [c[0] for c in cols_res.fetchall()]
        if "division_id" not in cols:
            print("Adding division_id to sj_category_tags...")
            await session.execute(text('''
                ALTER TABLE sj_category_tags 
                ADD COLUMN division_id INT DEFAULT NULL;
            '''))
            if "category_head_id" in cols:
                await session.execute(text('''
                    UPDATE sj_category_tags SET division_id = category_head_id WHERE division_id IS NULL;
                '''))
            await session.execute(text('''
                ALTER TABLE sj_category_tags
                ADD CONSTRAINT fk_cat_tags_division FOREIGN KEY (division_id) REFERENCES sj_divisions (id) ON DELETE SET NULL;
            '''))
        else:
            # Sync any division_id with category_head_id
            if "category_head_id" in cols:
                await session.execute(text('''
                    UPDATE sj_category_tags SET division_id = category_head_id WHERE division_id IS NULL AND category_head_id IS NOT NULL;
                '''))

        # Create sj_division_category_tags junction table
        print("Creating sj_division_category_tags table...")
        await session.execute(text('''
            CREATE TABLE IF NOT EXISTS sj_division_category_tags (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                division_id INT NOT NULL,
                category_tag_id INT NOT NULL,
                display_order INT NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT NULL,
                UNIQUE KEY uq_division_tag (division_id, category_tag_id),
                KEY fk_div_tag_division (division_id),
                KEY fk_div_tag_tag (category_tag_id),
                CONSTRAINT fk_div_tag_division FOREIGN KEY (division_id) REFERENCES sj_divisions (id) ON DELETE CASCADE,
                CONSTRAINT fk_div_tag_tag FOREIGN KEY (category_tag_id) REFERENCES sj_category_tags (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        '''))

        # Migrate data from sj_category_head_category_tags if present
        tbl_junc = await session.execute(text("SHOW TABLES LIKE 'sj_category_head_category_tags'"))
        if tbl_junc.fetchone():
            print("Migrating junction records from sj_category_head_category_tags...")
            await session.execute(text('''
                INSERT IGNORE INTO sj_division_category_tags (division_id, category_tag_id, display_order, created_at)
                SELECT category_head_id, category_tag_id, display_order, created_at
                FROM sj_category_head_category_tags;
            '''))

        # Ensure seed divisions exist: Stationery, Grocery, Toys, Electronics
        print("Checking default seed divisions...")
        seed_divisions = [
            ("Stationery", "School, Office & Creative Stationery products", 1),
            ("Grocery", "Daily essentials, food & household staples", 2),
            ("Toys", "Kids games, educational kits & creative play", 3),
            ("Electronics", "Gadgets, computing, audio & accessories", 4),
        ]
        for name, desc, order in seed_divisions:
            res = await session.execute(text("SELECT id FROM sj_divisions WHERE LOWER(name) = LOWER(:name)"), {"name": name})
            if not res.fetchone():
                import uuid
                await session.execute(text('''
                    INSERT INTO sj_divisions (external_id, name, description, display_order, is_active, created_at, updated_at)
                    VALUES (:ext, :name, :desc, :order, 1, NOW(), NOW())
                '''), {"ext": uuid.uuid4().hex[:16], "name": name, "desc": desc, "order": order})

        # Ensure all existing tags are linked to Stationery division if not linked
        stat_res = await session.execute(text("SELECT id FROM sj_divisions WHERE name = 'Stationery'"))
        stat_row = stat_res.fetchone()
        if stat_row:
            stat_id = stat_row[0]
            await session.execute(text('''
                UPDATE sj_category_tags SET division_id = :did WHERE division_id IS NULL;
            '''), {"did": stat_id})
            await session.execute(text('''
                INSERT IGNORE INTO sj_division_category_tags (division_id, category_tag_id, display_order, created_at)
                SELECT :did, id, 0, NOW() FROM sj_category_tags WHERE division_id = :did;
            '''), {"did": stat_id})

        await session.commit()
        print("Divisions migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
