from app.models.user import User
from typing import TYPE_CHECKING, Any
from app.models.schemas import UserInternalCreate, UserInternalUpdate, UserUpdate, UserCreate
from typing import Dict, Optional

from app.db.storage_factory import get_storage
from app.utils.auth import get_password_hash, verify_password
from app.utils.logger import logger
from app.utils.referral import get_unique_referral_code

if TYPE_CHECKING:
    from app.models.daos import UserInternalUpdate
    


class UserRepository:
    def __init__(self):
        self.storage = get_storage("users")

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        users_data = await self.storage.findAll(query or {}, skip=skip, limit=limit)
        return users_data

    async def findById(self, id: str) -> Optional[User]:
        data = await self.storage.findById(id)
        return data

    async def findOne(self, query: dict) -> Optional[User]:
        data = await self.storage.findOne(query)
        return data

    async def findByEmail(self, email: str) -> Optional[User]:
        data = await self.storage.findOne({"email": email.lower()})
        return data

    async def findByPhone(self, phone: str):
        if not phone:
            return None
        # Normalize phone number by removing non-digit characters
        normalized_phone = "".join(filter(str.isdigit, phone))
        # Try exact match first, then the most common format variants.
        # This covers: raw input, digits-only, +91-prefixed, and 91-prefixed formats
        # without falling back to a full-table scan.
        candidates = {phone, normalized_phone}
        if len(normalized_phone) == 10:
            candidates.add(f"+91{normalized_phone}")
            candidates.add(f"91{normalized_phone}")
        elif normalized_phone.startswith("91") and len(normalized_phone) == 12:
            candidates.add(normalized_phone[2:])
            candidates.add(f"+{normalized_phone}")
        elif normalized_phone.startswith("0") and len(normalized_phone) == 11:
            candidates.add(normalized_phone[1:])

        for candidate in candidates:
            user = await self.storage.findOne({"phone": candidate})
            if user:
                return user
        return None

    async def create(self, user_data: UserCreate):
        # Check if user with email already exists (only if email is provided)
        email = user_data.email
        if email:
            existing = await self.findByEmail(email)
            if existing:
                raise ValueError("User with this email already exists")

        # Check if user with phone already exists
        if user_data.phone:
            existing_phone = await self.findByPhone(user_data.phone)
            if existing_phone:
                raise ValueError("User with this phone number already exists")

        # Password is required for account creation
        password_val = user_data.password
        if not password_val:
            raise ValueError("Password is required")
        hashed_password = get_password_hash(password_val)

        # Generate display user ID. Using max(userId)+1 rather than count+1 means
        # that even if two registrations race, the one that commits second will see
        # the first one's row and pick a higher number. Not atomic, but far safer
        # than count-based allocation which silently produces duplicates when rows
        # are deleted and re-added.
        try:
            user_id = await self.storage.getNextUserId()
        except Exception:
            logger.error(
                "Failed to generate next userId; falling back to userId=1.",
                exc_info=True,
            )
            user_id = 1
        user_id_formatted = f"USER-{user_id}"

        # Determine approval status
        role = (user_data.role if user_data.role is not None else "customer")
        approval_status = "pending" if role == "wholesaler" else "approved"

        # Generate referral code
        referral_code = await get_unique_referral_code(self)

        # Name and email are optional; default name to "Customer" if not provided
        name = user_data.name or "Customer"
        email_val = email.lower() if email else None

        user_model = UserInternalCreate(
            user_id=user_id,
            user_id_formatted=user_id_formatted,
            name=name,
            email=email_val,
            password=hashed_password,
            role=role,
            phone=(user_data.phone if user_data.phone is not None else ""),
            company_name=(user_data.company_name if user_data.company_name is not None else ""),
            address=(user_data.address if user_data.address is not None else {}),
            saved_addresses=(user_data.saved_addresses if user_data.saved_addresses is not None else []),
            is_active=(user_data.is_active if user_data.is_active is not None else True),
            approval_status=(user_data.approval_status if user_data.approval_status is not None else approval_status),
            is_deactivated=(user_data.is_deactivated if user_data.is_deactivated is not None else False),
            credit_limit=(user_data.credit_limit if user_data.credit_limit is not None else 0),
            credit_used=(user_data.credit_used if user_data.credit_used is not None else 0),
            payment_terms=(user_data.payment_terms if user_data.payment_terms is not None else "30"),
            assigned_salesperson=user_data.assigned_salesperson,
            referral_code=referral_code,
            is_email_verified=(user_data.is_email_verified if user_data.is_email_verified is not None else False),
            is_on_duty=(user_data.is_on_duty if user_data.is_on_duty is not None else False),
            is_seller_admin=(user_data.is_seller_admin if user_data.is_seller_admin is not None else False),
            service_area_zones=(user_data.service_area_zones if user_data.service_area_zones is not None else []),
            commission_override_pct=user_data.commission_override_pct,
            upi_id=user_data.upi_id,
            qr_code_url=user_data.qr_code_url,
            gstin=user_data.gstin,
        )

        if user_model.address and user_model.address not in (user_model.saved_addresses or []):
            if user_model.saved_addresses is None:
                user_model.saved_addresses = []
            user_model.saved_addresses.append(user_model.address)

        created_dict = await self.storage.create(user_model)
        return created_dict

    async def update(self, id: str, update_data: 'UserInternalUpdate'):
        # Don't allow updating email to an existing one
        email_val = update_data.email
        if email_val is not None:
            existing = await self.findByEmail(email_val)
            if existing and existing.id != id:
                raise ValueError("Email already in use")
            update_data.email = email_val.lower()

        # Don't allow updating phone to an existing one
        phone_val = update_data.phone
        if phone_val is not None:
            existing_phone = await self.findByPhone(phone_val)
            if existing_phone and existing_phone.id != id:
                raise ValueError("Phone number already in use")

        # Hash password if provided
        if update_data.password is not None:
            update_data.password = get_password_hash(update_data.password)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)

    async def addSavedAddress(self, user_id: str, address: 'SavedAddress'):
        """Add a new address to user's saved addresses list uniquely."""
        user = await self.findById(user_id)
        if not user:
            return None

        saved_addresses = (user.saved_addresses if user.saved_addresses is not None else [])

        # Simple duplicate check
        is_duplicate = False
        for sa in saved_addresses:
            if (
                sa.street == address.street
                and sa.city == address.city
                and sa.zip_code == address.zip_code
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            saved_addresses.append(address)
            await self.update(user_id, UserUpdate(savedAddresses=saved_addresses))

        return saved_addresses

    def compare_password(self, user: 'User', candidate_password: str) -> bool:
        if not user or not user.password:
            logger.warning(
                "compare_password: User or password missing, userId=%s, hasPassword=%s",
                user.id if user else None,
                bool(user.password if user else False),
            )
            return False
        if not candidate_password:
            logger.warning("compare_password: Candidate password missing")
            return False
        try:
            return verify_password(candidate_password, (user.password if user.password is not None else ""))
        except Exception as e:
            logger.error("compare_password error: %s", str(e), exc_info=True)
            return False

    async def ensure_referral_codes(self):
        """Ensure all users have a unique referral code. Use this for migration."""
        users = await self.findAll()
        updated_count = 0
        for user in users:
            if not user.referral_code:
                code = await get_unique_referral_code(self)
                await self.update(user.id, UserUpdate(referralCode=code))
                updated_count += 1
        return updated_count

    async def adjust_credit(self, user_id: str, amount: float) -> Optional[User]:
        """
        Atomically adjust user credit (positive = consume, negative = refund).
        Uses SELECT FOR UPDATE on the relational table.
        """
        from sqlalchemy import text
        from datetime import datetime, timezone
        from app.config.database import get_async_session_factory

        factory = get_async_session_factory()
        if not factory:
            return None

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, credit_used, credit_limit FROM {self.storage.TABLE} WHERE id = :id FOR UPDATE"),
                {"id": user_id},
            )
            row = result.fetchone()
            if not row:
                return None

            new_credit_used = max(0, float(row.credit_used) + amount)
            now = datetime.now(timezone.utc).isoformat()
            
            await session.execute(
                text(f"UPDATE {self.storage.TABLE} SET credit_used = :cu, updated_at = :u WHERE id = :id"),
                {"cu": new_credit_used, "u": now, "id": user_id},
            )
            await session.commit()

        return await self.findById(user_id)


user_repository = UserRepository()




