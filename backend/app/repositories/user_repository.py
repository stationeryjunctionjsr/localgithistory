from app.models.user import User
from typing import Any
from app.models.schemas import UserInternalCreate, UserInternalUpdate, UserUpdate, UserCreate
from typing import Dict, Optional

from app.db.storage_factory import get_storage
from app.utils.auth import get_password_hash, verify_password
from app.utils.logger import logger
from app.utils.referral import get_unique_referral_code


class UserRepository:
    def __init__(self):
        self.storage = get_storage("users")

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        users_data = await self.storage.findAll(query or {}, skip=skip, limit=limit)
        return users_data

    async def findById(self, id: str) -> Optional[User]:
        data = await self.storage.findById(id)
        return data

    async def findOne(self, query: Any) -> Optional[User]:
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

    async def create(self, user_data: Any):
        if isinstance(user_data, dict):
            if "role" in user_data and hasattr(user_data["role"], "value"):
                user_data["role"] = user_data["role"].value
            user_data = UserCreate(**user_data)
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
            all_ids = [u.userId for u in await self.storage.findAll() if isinstance(u.userId, int)]
            user_id = (max(all_ids) + 1) if all_ids else 1
        except Exception:
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
            userId=user_id,
            userIdFormatted=user_id_formatted,
            name=name,
            email=email_val,
            password=hashed_password,
            role=role,
            phone=(user_data.phone if user_data.phone is not None else ""),
            companyName=(user_data.companyName if user_data.companyName is not None else ""),
            address=(user_data.address if user_data.address is not None else {}),
            savedAddresses=(user_data.savedAddresses if user_data.savedAddresses is not None else []),
            isActive=(user_data.isActive if user_data.isActive is not None else True),
            approvalStatus=(user_data.approvalStatus if user_data.approvalStatus is not None else approval_status),
            isDeactivated=(user_data.isDeactivated if user_data.isDeactivated is not None else False),
            creditLimit=(user_data.creditLimit if user_data.creditLimit is not None else 0),
            creditUsed=(user_data.creditUsed if user_data.creditUsed is not None else 0),
            paymentTerms=(user_data.paymentTerms if user_data.paymentTerms is not None else "30"),
            assignedSalesperson=user_data.assignedSalesperson,
            referralCode=referral_code,
            isEmailVerified=(user_data.isEmailVerified if user_data.isEmailVerified is not None else False),
        )

        if user_model.address and user_model.address not in user_model.savedAddresses:
            user_model.savedAddresses.append(user_model.address)

        created_dict = await self.storage.create(user_model)
        from app.models.schemas import UserResponse
        return UserResponse.model_validate(created_dict) if isinstance(created_dict, dict) else created_dict

    async def update(self, id: str, update_data: Any):
        # Don't allow updating email to an existing one
        email_val = update_data.get("email") if isinstance(update_data, dict) else getattr(update_data, "email", None)
        if email_val is not None:
            existing = await self.findByEmail(email_val)
            if existing and existing.id != id:
                raise ValueError("Email already in use")
            email_val = email_val.lower()

        # Don't allow updating phone to an existing one
        phone_val = update_data.get("phone") if isinstance(update_data, dict) else getattr(update_data, "phone", None)
        if phone_val is not None:
            existing_phone = await self.findByPhone(phone_val)
            if existing_phone and existing_phone.id != id:
                raise ValueError("Phone number already in use")

        # Hash password if provided
        if getattr(update_data, "password", getattr(update_data, "get", lambda x: None)("password")) is not None:
            if isinstance(update_data, dict): update_data["password"] = get_password_hash(update_data["password"])
            else: update_data.password = get_password_hash(update_data.password)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)

    async def addSavedAddress(self, user_id: str, address: Any):
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
                and sa.zipCode == address.zipCode
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            saved_addresses.append(address)
            await self.update(user_id, UserUpdate(savedAddresses=saved_addresses))

        return saved_addresses

    def compare_password(self, user: Any, candidate_password: str) -> bool:
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




