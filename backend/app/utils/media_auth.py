from typing import Optional
from app.models.user import User

async def verify_media_ownership(key_or_path: str, current_user: Optional[User]) -> bool:
    if not current_user:
        return False
    
    if current_user.role in ["super_admin", "admin"]:
        return True

    # key_or_path could be an OCI key or a local /uploads/ path
    # e.g., "SJ_LOCAL/invoices/invoice-1234.pdf" or "/uploads/SJ_LOCAL/invoices/invoice-1234.pdf"
    
    from app.repositories.order_repository import order_repository
    from app.repositories.payment_repository import payment_repository

    if "invoices/" in key_or_path:
        # Check order ownership
        # Both Order.invoice_path and SubOrder might have invoice_paths (usually just Order)
        # Try to find an order where invoice_path contains this key
        
        # It's safer to extract the filename
        filename = key_or_path.split("/")[-1]
        
        orders = await order_repository.findAll({"user": str(current_user.id)})
        for o in orders:
            if o.invoice_path and filename in o.invoice_path:
                return True
        return False
        
    if "payments/" in key_or_path:
        filename = key_or_path.split("/")[-1]
        user_id_val = current_user.user_id if current_user.user_id else str(current_user.id)
        payments = await payment_repository.findAll({"userId": user_id_val})
        for p in payments:
            if p.payment_entries:
                for entry in p.payment_entries:
                    if entry.image and filename in entry.image:
                        return True
        return False
        
    # Default to deny if we can't determine
    return False
