import os

filepath = 'backend/app/db/mysql_category_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'await self._replace_children(session, cid, merged)',
    '''class DummyMerged:
                pass
            dummy_merged = DummyMerged()
            dummy_merged.images = update_data.images if update_data.images is not None else existing.images
            dummy_merged.subCategories = update_data.subCategories if update_data.subCategories is not None else existing.sub_categories
            dummy_merged.categoryTags = update_data.categoryTags if update_data.categoryTags is not None else existing.category_tags
            await self._replace_children(session, cid, dummy_merged)'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
