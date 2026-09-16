import os
import re

filepath = 'backend/app/db/mysql_flat_daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace update method body for MySQLStockReservationDAO
replacement = '''    async def update(self, id: str, data: Any) -> Optional[StockReservation]:
        existing = await self.findById(id)
        if not existing:
            return None
        existing_dict = existing if isinstance(existing, dict) else existing.__dict__
        data_dict = data if isinstance(data, dict) else getattr(data, '__dict__', {})
        merged = {**existing_dict, **data_dict}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        product_id = merged.get("productId") or merged.get("product_id")
        if product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = product_id
            
        user_id = merged.get("userId") or merged.get("user_id")
        if user_id is not None:
            updates.append("user_id = :userId")
            params["userId"] = user_id
            
        quantity = merged.get("quantity")
        if quantity is not None:
            updates.append("quantity = :quantity")
            params["quantity"] = quantity
            
        status = merged.get("status")
        if status is not None:
            updates.append("status = :status")
            params["status"] = status
            
        expires_at = merged.get("expiresAt") or merged.get("expires_at")
        if expires_at is not None:
            updates.append("expires_at = :expiresAt")
            params["expiresAt"] = expires_at

        if not updates:
            return existing

        set_clause = ", ".join(updates)
        q = f"UPDATE stock_reservations SET {set_clause} WHERE id = :id"
        await self.db.execute(text(q), params)
        return await self.findById(id)
'''

content = re.sub(
    r'    async def update\(self, id: str, data: StockReservationsInternalUpdate\) -> Optional\[StockReservation\]:.*?return await self\.findById\(id\)',
    replacement,
    content,
    flags=re.DOTALL
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
