import os

filepath = 'backend/app/db/mysql_category_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_block = r'''        # Convert existing Category to dict for merging, then instantiate the Update model
        from app.models.daos import CategoryInternalUpdate
        existing_dict = existing\.model_dump\(by_alias=True\)
        update_dict = update_data\.model_dump\(exclude_unset=True\)
        merged_dict = \{\*\*existing_dict, \*\*update_dict\}
        merged = CategoryInternalUpdate\(\*\*merged_dict\)

        factory = self\._factory\(\)
        now = now_utc\(\)
        cid = int\(id\) if str\(id\)\.isdigit\(\) else None
        async with factory\(\) as session:
            await session\.execute\(
                text\(
                    f"""
                    UPDATE \{self\.TABLE\} SET
                        name = :name,
                        description = :description,
                        is_active = :is_active,
                        category_tag = :category_tag,
                        minimum_quantity = :minimum_quantity,
                        gst = :gst,
                        is_returnable = :is_returnable,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                \),
                \{
                    "id": cid,
                    "name": merged\.name,
                    "description": merged\.description,
                    "is_active": int\(bool\(merged\.isActive if merged\.isActive is not None else True\)\),
                    "category_tag": merged\.categoryTag,
                    "minimum_quantity": merged\.minimumQuantity,
                    "gst": merged\.gst,
                    "is_returnable": int\(bool\(merged\.isReturnable if merged\.isReturnable is not None else True\)\),
                    "updated_at": now,
                \},
            \)'''

new_block = '''        factory = self._factory()
        now = now_utc()
        cid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        is_active = :is_active,
                        category_tag = :category_tag,
                        minimum_quantity = :minimum_quantity,
                        gst = :gst,
                        is_returnable = :is_returnable,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "name": update_data.name if update_data.name is not None else existing.name,
                    "description": update_data.description if update_data.description is not None else existing.description,
                    "is_active": int(bool(update_data.isActive if update_data.isActive is not None else existing.is_active)),
                    "category_tag": update_data.categoryTag if update_data.categoryTag is not None else existing.category_tag,
                    "minimum_quantity": update_data.minimumQuantity if update_data.minimumQuantity is not None else existing.minimum_quantity,
                    "gst": update_data.gst if update_data.gst is not None else existing.gst,
                    "is_returnable": int(bool(update_data.isReturnable if update_data.isReturnable is not None else existing.is_returnable)),
                    "updated_at": now,
                },
            )'''

content = re.sub(old_block, new_block, content, flags=re.DOTALL)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
