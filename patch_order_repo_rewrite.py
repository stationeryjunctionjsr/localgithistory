import os
filepath = 'backend/app/repositories/order_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('    async def update(self, id: str')
end_idx = content.find('    async def get_my_orders(', start_idx)

new_update = '''    async def update(self, id: str, update_data: Any):
        status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
        
        if status == "out_for_delivery":
            shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
            if shipped_at is None:
                if isinstance(update_data, dict):
                    update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()
                else:
                    update_data.shippedAt = datetime.now(timezone.utc).isoformat()

        if status == "delivered":
            delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
            if delivered_at is None:
                if isinstance(update_data, dict):
                    update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()
                else:
                    update_data.deliveredAt = datetime.now(timezone.utc).isoformat()
            
            order = await self.findById(id)
            if order and getattr(order, "paymentMethod", None) == "cod":
                payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
                if payment_status is None:
                    if isinstance(update_data, dict):
                        update_data["paymentStatus"] = "paid"
                    else:
                        update_data.paymentStatus = "paid"

        return await self.storage.update(id, update_data)

'''
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content[:start_idx] + new_update + content[end_idx:])
