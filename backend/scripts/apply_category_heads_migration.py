"""
Migration script to add sj_category_heads, sj_category_head_category_tags,
and relational foreign key columns category_head_id to sj_category_tags,
and category_tag_id to sj_categories and sj_category_category_tags.
"""

import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run_migration():
    factory = get_async_session_factory()
    if not factory:
        print("Database not configured.")
        return

    async with factory() as session:
        print("Creating sj_category_heads table if not exists...")
        await session.execute(text('''
            CREATE TABLE IF NOT EXISTS sj_category_heads (
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

        # Add category_head_id to sj_category_tags
        cols_res = await session.execute(text('DESCRIBE sj_category_tags'))
        cols = [c[0] for c in cols_res.fetchall()]
        if 'category_head_id' not in cols:
            print("Adding category_head_id to sj_category_tags...")
            await session.execute(text('''
                ALTER TABLE sj_category_tags 
                ADD COLUMN category_head_id INT DEFAULT NULL,
                ADD CONSTRAINT fk_cat_tags_head FOREIGN KEY (category_head_id) REFERENCES sj_category_heads (id) ON DELETE SET NULL;
            '''))

        # Create sj_category_head_category_tags junction table
        print("Creating sj_category_head_category_tags table if not exists...")
        await session.execute(text('''
            CREATE TABLE IF NOT EXISTS sj_category_head_category_tags (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                category_head_id INT NOT NULL,
                category_tag_id INT NOT NULL,
                display_order INT NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT NULL,
                UNIQUE KEY uq_head_tag (category_head_id, category_tag_id),
                KEY fk_chct_head (category_head_id),
                KEY fk_chct_tag (category_tag_id),
                CONSTRAINT fk_chct_head FOREIGN KEY (category_head_id) REFERENCES sj_category_heads (id) ON DELETE CASCADE,
                CONSTRAINT fk_chct_tag FOREIGN KEY (category_tag_id) REFERENCES sj_category_tags (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        '''))

        # Add category_tag_id to sj_categories
        cols_cat_res = await session.execute(text('DESCRIBE sj_categories'))
        cols_cat = [c[0] for c in cols_cat_res.fetchall()]
        if 'category_tag_id' not in cols_cat:
            print("Adding category_tag_id to sj_categories...")
            await session.execute(text('''
                ALTER TABLE sj_categories 
                ADD COLUMN category_tag_id INT DEFAULT NULL,
                ADD CONSTRAINT fk_cat_category_tag FOREIGN KEY (category_tag_id) REFERENCES sj_category_tags (id) ON DELETE SET NULL;
            '''))

        # Add category_tag_id to sj_category_category_tags
        cols_cct_res = await session.execute(text('DESCRIBE sj_category_category_tags'))
        cols_cct = [c[0] for c in cols_cct_res.fetchall()]
        if 'category_tag_id' not in cols_cct:
            print("Adding category_tag_id to sj_category_category_tags...")
            await session.execute(text('''
                ALTER TABLE sj_category_category_tags 
                ADD COLUMN category_tag_id INT DEFAULT NULL,
                ADD CONSTRAINT fk_cct_category_tag FOREIGN KEY (category_tag_id) REFERENCES sj_category_tags (id) ON DELETE CASCADE;
            '''))

        await session.commit()
        print("Category Heads migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
