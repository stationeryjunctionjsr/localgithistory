import re

with open('app/db/mysql_returnRequests_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_replace = """    async def _replace_children(self, session, row_id: int, data: Any):
        fields = data.model_fields_set if hasattr(data, 'model_fields_set') else set(dir(data))
        
        if 'items' in fields:
            await session.execute(text(f"DELETE FROM sj_return_request_items WHERE parent_id = :id"), {"id": row_id})
            child_list = data.items if hasattr(data, 'items') else []
            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = getattr(item, 'productId', None)
                    p["v1"] = getattr(item, 'quantity', None)
                    p["v2"] = getattr(item, 'reason', None)
                    await session.execute(text(f"INSERT INTO sj_return_request_items (parent_id, product_id, quantity, reason) VALUES (:id, :v0, :v1, :v2)"), p)

        if 'valetDeclineHistory' in fields:
            await session.execute(text(f"DELETE FROM sj_return_request_valet_declines WHERE parent_id = :id"), {"id": row_id})
            child_list = data.valetDeclineHistory if hasattr(data, 'valetDeclineHistory') else []
            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = getattr(item, 'valetId', None)
                    p["v1"] = getattr(item, 'reason', None)
                    p["v2"] = getattr(item, 'declinedAt', None)
                    await session.execute(text(f"INSERT INTO sj_return_request_valet_declines (parent_id, valet_id, reason, declined_at) VALUES (:id, :v0, :v1, :v2)"), p)
"""

text = re.sub(r"    async def _replace_children\(self, session, row_id: int, data: Any\):.*", new_replace, text, flags=re.DOTALL)

with open('app/db/mysql_returnRequests_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
