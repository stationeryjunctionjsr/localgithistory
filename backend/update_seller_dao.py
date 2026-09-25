import re

with open('app/db/mysql_seller_payout_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add imports
text = text.replace('from typing import Dict, Any', 'from typing import Dict, Any, List, Optional\nfrom app.models.schemas import SellerPayoutDetailResponse')

# Update _map_row
old_map = '''    def _map_row(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": str(row.id),
            "external_id": row.external_id,
            "sellerId": row.seller_id,
            "amount": float(row.amount) if row.amount is not None else 0.0,
            "periodStart": row.period_start.isoformat() if row.period_start else None,
            "periodEnd": row.period_end.isoformat() if row.period_end else None,
            "status": row.status if row.status else 'pending_payment',
            "paymentMethod": row.payment_method,
            "paymentReference": row.payment_reference,
            "adminPaidAt": row.admin_paid_at.isoformat() if row.admin_paid_at else None,
            "adminPaidBy": row.admin_paid_by,
            "sellerReceivedAt": row.seller_received_at.isoformat() if row.seller_received_at else None,
            "notes": row.notes,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }'''

new_map = '''    def _map_row(self, row) -> SellerPayoutDetailResponse:
        return SellerPayoutDetailResponse(
            id=str(row.id),
            sellerId=row.seller_id,
            amount=float(row.amount) if row.amount is not None else 0.0,
            periodStart=row.period_start.isoformat() + "Z" if row.period_start else None,
            periodEnd=row.period_end.isoformat() + "Z" if row.period_end else None,
            status=row.status if row.status else 'pending_payment',
            paymentMethod=row.payment_method,
            paymentReference=row.payment_reference,
            adminPaidAt=row.admin_paid_at.isoformat() + "Z" if row.admin_paid_at else None,
            adminPaidBy=row.admin_paid_by,
            sellerReceivedAt=row.seller_received_at.isoformat() + "Z" if row.seller_received_at else None,
            notes=row.notes,
            createdAt=row.created_at.isoformat() + "Z" if row.created_at else None,
            updatedAt=row.updated_at.isoformat() + "Z" if row.updated_at else None,
        )'''
text = text.replace(old_map, new_map)

# Change return types
text = text.replace('def findAll(self, query: Dict = None) -> list:', 'def findAll(self, query: Dict = None) -> List[SellerPayoutDetailResponse]:')
text = text.replace('def findById(self, id: str) -> Dict:', 'def findById(self, id: str) -> Optional[SellerPayoutDetailResponse]:')
text = text.replace('def update(self, id: str, data: SellerPayoutInternalUpdate) -> Dict:', 'def update(self, id: str, data: SellerPayoutInternalUpdate) -> Optional[SellerPayoutDetailResponse]:')

# Update _handle_field logic in update
old_handle = '''        def _handle_field(api_k, db_k, new_val, is_date=False):
            if new_val is not None:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = _parse_dt(new_val) if is_date else new_val
            else:
                fallback_val = existing.get(api_k)
                if fallback_val is not None:
                    updates.append(f"{db_k} = :{api_k}")
                    params[api_k] = _parse_dt(fallback_val) if is_date else fallback_val

        _handle_field("sellerId", "seller_id", data.seller_id)
        _handle_field("amount", "amount", data.amount)
        _handle_field("periodStart", "period_start", data.period_start, True)
        _handle_field("periodEnd", "period_end", data.period_end, True)
        _handle_field("status", "status", data.status)
        _handle_field("paymentMethod", "payment_method", data.payment_method)
        _handle_field("paymentReference", "payment_reference", data.payment_reference)
        _handle_field("adminPaidAt", "admin_paid_at", data.admin_paid_at, True)
        _handle_field("adminPaidBy", "admin_paid_by", data.admin_paid_by)
        _handle_field("sellerReceivedAt", "seller_received_at", data.seller_received_at, True)
        _handle_field("notes", "notes", data.notes)'''

new_handle = '''        def _handle_field(api_k, db_k, new_val, existing_val, is_date=False):
            if new_val is not None:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = _parse_dt(new_val) if is_date else new_val
            else:
                if existing_val is not None:
                    updates.append(f"{db_k} = :{api_k}")
                    params[api_k] = _parse_dt(existing_val) if is_date else existing_val

        _handle_field("sellerId", "seller_id", data.seller_id, existing.seller_id)
        _handle_field("amount", "amount", data.amount, existing.amount)
        _handle_field("periodStart", "period_start", data.period_start, existing.period_start, True)
        _handle_field("periodEnd", "period_end", data.period_end, existing.period_end, True)
        _handle_field("status", "status", data.status, existing.status)
        _handle_field("paymentMethod", "payment_method", data.payment_method, existing.payment_method)
        _handle_field("paymentReference", "payment_reference", data.payment_reference, existing.payment_reference)
        _handle_field("adminPaidAt", "admin_paid_at", data.admin_paid_at, existing.admin_paid_at, True)
        _handle_field("adminPaidBy", "admin_paid_by", data.admin_paid_by, existing.admin_paid_by)
        _handle_field("sellerReceivedAt", "seller_received_at", data.seller_received_at, existing.seller_received_at, True)
        _handle_field("notes", "notes", data.notes, existing.notes)'''

text = text.replace(old_handle, new_handle)

with open('app/db/mysql_seller_payout_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS")
