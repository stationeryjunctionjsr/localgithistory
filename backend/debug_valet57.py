import re

with open('app/db/mysql_returnRequests_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_update = """    async def update(self, id: str, data: Any) -> Any:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}
        
        field_map = {
            "returnId": "return_id",
            "orderId": "order_id",
            "userId": "user_id",
            "paymentMethod": "payment_method",
            "upiPaymentScreenshot": "upi_payment_screenshot",
            "notes": "notes",
            "status": "status",
            "valetId": "valet_id",
            "sellerId": "seller_id",
            "deliverySlotId": "delivery_slot_id",
            "deliverySlotConfigId": "delivery_slot_config_id",
            "deliverySlotDate": "delivery_slot_date",
            "pendingValetId": "pending_valet_id",
            "valetAssignedAt": "valet_assigned_at",
            "valetCascadeCount": "valet_cascade_count",
            "deliveryCharge": "delivery_charge"
        }
        
        if hasattr(data, 'model_dump'):
            dump = data.model_dump(exclude_unset=True)
            for k, v in dump.items():
                if k in field_map:
                    updates.append(f"{field_map[k]} = :s_{k}")
                    params[f"s_{k}"] = v
                    
        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(str(id))"""

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
            await session.execute(text(f"DELETE FROM sj_return_valet_declines WHERE parent_id = :id"), {"id": row_id})
            child_list = data.valetDeclineHistory if hasattr(data, 'valetDeclineHistory') else []
            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = getattr(item, 'valetId', None)
                    p["v1"] = getattr(item, 'reason', None)
                    await session.execute(text(f"INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason) VALUES (:id, :v0, :v1)"), p)
"""

text = re.sub(r"    async def update\(self, id: str, data: Any\) -> Any:.*?(?=\n    async def delete)", new_update + "\n", text, flags=re.DOTALL)
text = re.sub(r"    async def _replace_children\(self, session, row_id: int, data: Any\):.*?(?=\n    async def _fetch_children)", new_replace, text, flags=re.DOTALL)

with open('app/db/mysql_returnRequests_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
