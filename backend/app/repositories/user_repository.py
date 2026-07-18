from typing import Dict, Optional

from app.db.storage_factory import get_storage
from app.utils.auth import get_password_hash, verify_password
from app.utils.logger import logger
from app.utils.referral import get_unique_referral_code


class UserRepository:
    def __init__(self):
        self.storage = get_storage("users")

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findOne(self, query: Dict):
        return await self.storage.findOne(query)

    async def findByEmail(self, email: str):
        return await self.storage.findOne({"email": email.lower()})

    async def findByPhone(self, phone: str):
        if not phone:
            return None
        # Normalize phone number by removing non-digit characters
        normalized_phone = "".join(filter(str.isdigit, phone))
        # Try to find by exact match first, then try normalized version
        user = await self.storage.findOne({"phone": phone})
        if not user and normalized_phone != phone:
            user = await self.storage.findOne({"phone": normalized_phone})
        # If still not found, check all users and normalize their phones for comparison
        if not user:
            all_users = await self.storage.findAll()
            for u in all_users:
                if u.get("phone"):
                    user_phone = "".join(filter(str.isdigit, u.get("phone", "")))
                    if user_phone == normalized_phone:
                        return u
        return user

    async def create(self, user_data: Dict):
        # Check if user with email already exists (only if email is provided)
        email = user_data.get("email")
        if email:
            existing = await self.findByEmail(email)
            if existing:
                raise ValueError("User with this email already exists")

        # Check if user with phone already exists
        if user_data.get("phone"):
            existing_phone = await self.findByPhone(user_data["phone"])
            if existing_phone:
                raise ValueError("User with this phone number already exists")

        # Password is required for account creation
        password_val = user_data.get("password")
        if not password_val:
            raise ValueError("Password is required")
        hashed_password = get_password_hash(password_val)

        # Generate incremental user ID starting from 1
        all_users = await self.storage.findAll()
        max_id = 0
        for user in all_users:
            if user.get("userId") and isinstance(user.get("userId"), int):
                max_id = max(max_id, user.get("userId", 0))
        user_id = max_id + 1
        user_id_formatted = f"USER-{user_id}"

        # Determine approval status
        role = user_data.get("role", "customer")
        approval_status = "pending" if role == "wholesaler" else "approved"

        # Generate referral code
        referral_code = await get_unique_referral_code(self)

        # Name and email are optional; default name to "Customer" if not provided
        name = user_data.get("name") or "Customer"
        email_val = email.lower() if email else None

        user = {
            "userId": user_id,  # Keep numeric ID for internal use
            "userIdFormatted": user_id_formatted,  # Display format: USER-1, USER-2, etc.
            "name": name,
            "email": email_val,
            "password": hashed_password,
            "role": role,
            "phone": user_data.get("phone", ""),
            "companyName": user_data.get("companyName", ""),
            "address": user_data.get("address", {}),
            "savedAddresses": user_data.get("savedAddresses", []),
            "isActive": user_data.get("isActive", True),
            "approvalStatus": user_data.get("approvalStatus", approval_status),
            "isDeactivated": user_data.get("isDeactivated", False),
            "creditLimit": user_data.get("creditLimit", 0),
            "creditUsed": user_data.get("creditUsed", 0),
            "paymentTerms": user_data.get("paymentTerms", "30"),
            "assignedSalesperson": user_data.get("assignedSalesperson"),
            "referralCode": referral_code,
            "isEmailVerified": user_data.get("isEmailVerified", False),
        }

        # If an address is provided, add it to savedAddresses if not already there
        if user["address"] and user["address"] not in user["savedAddresses"]:
            user["savedAddresses"].append(user["address"])

        return await self.storage.create(user)

    async def update(self, id: str, update_data: Dict):
        # Don't allow updating email to an existing one
        if "email" in update_data:
            existing = await self.findByEmail(update_data["email"])
            if existing and existing.get("_id") != id:
                raise ValueError("Email already in use")
            update_data["email"] = update_data["email"].lower()

        # Don't allow updating phone to an existing one
        if "phone" in update_data:
            existing_phone = await self.findByPhone(update_data["phone"])
            if existing_phone and existing_phone.get("_id") != id:
                raise ValueError("Phone number already in use")

        # Hash password if provided
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)

    async def addSavedAddress(self, user_id: str, address: Dict):
        """Add a new address to user's saved addresses list uniquely."""
        user = await self.findById(user_id)
        if not user:
            return None

        saved_addresses = user.get("savedAddresses", [])

        # Simple duplicate check
        is_duplicate = False
        for sa in saved_addresses:
            if (
                sa.get("street") == address.get("street")
                and sa.get("city") == address.get("city")
                and sa.get("zipCode") == address.get("zipCode")
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            saved_addresses.append(address)
            await self.update(user_id, {"savedAddresses": saved_addresses})

        return saved_addresses

    def compare_password(self, user: Dict, candidate_password: str) -> bool:
        if not user or not user.get("password"):
            logger.warning(
                "compare_password: User or password missing, userId=%s, hasPassword=%s",
                user.get("_id") if user else None,
                bool(user.get("password") if user else False),
            )
            return False
        if not candidate_password:
            logger.warning("compare_password: Candidate password missing")
            return False
        try:
            return verify_password(candidate_password, user.get("password", ""))
        except Exception as e:
            logger.error("compare_password error: %s", str(e), exc_info=True)
            return False

    async def ensure_referral_codes(self):
        """Ensure all users have a unique referral code. Use this for migration."""
        users = await self.findAll()
        updated_count = 0
        for user in users:
            if not user.get("referralCode"):
                code = await get_unique_referral_code(self)
                await self.update(user["_id"], {"referralCode": code})
                updated_count += 1
        return updated_count


user_repository = UserRepository()
