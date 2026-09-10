"""
Oracle DAO for sj_users. Returns dicts with _id (external_id) and same shape as JSON.
All queries are parameterized. Uses numeric PK internally; API sees only external_id.
"""

from app.config.settings import settings
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory


def _row_to_dict(r) -> Dict:
    def clob_to_val(c):
        if c is None:
            return None
        if hasattr(c, "read"):
            return c.read()
        return c

    def parse_json(s):
        if s is None:
            return None
        import json

        try:
            return json.loads(s) if isinstance(s, str) else s
        except Exception:
            return None

    def clean_terms(t):
        if not t:
            return None
        t_str = str(t).replace("net_", "")
        return int(t_str) if t_str.isdigit() else None

    address = parse_json(clob_to_val(r.address))
    saved_addresses = parse_json(clob_to_val(r.saved_addresses))
    return {
        "_id": str(r.user_id),
        "userId": r.user_id,
        "userIdFormatted": r.user_id_formatted or (f"USER-{r.user_id}" if r.user_id else None),
        "name": r.name,
        "email": r.email,
        "password": r.password_hash,
        "role": r.role,
        "phone": r.phone or "",
        "companyName": r.company_name,
        "address": address or {},
        "savedAddresses": saved_addresses or [],
        "isActive": bool(r.is_active) if r.is_active is not None else True,
        "approvalStatus": r.approval_status,
        "isDeactivated": bool(r.is_deactivated) if r.is_deactivated is not None else False,
        "creditLimit": float(r.credit_limit) if r.credit_limit is not None else 0,
        "creditUsed": float(r.credit_used) if r.credit_used is not None else 0,
        "paymentTerms": clean_terms(r.payment_terms),
        "assignedSalesperson": r.assigned_salesperson,
        "isEmailVerified": bool(r.is_email_verified) if r.is_email_verified is not None else False,
        "referralCode": r.referral_code,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
    }


class OracleUserDAO:
    """Implements same interface as FileStorage for 'users' collection."""

    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_users{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _build_query_conditions(self, query: Dict) -> tuple[str, Dict]:
        where_clauses = []
        params = {}

        if "role" in query:
            where_clauses.append("role = :role")
            params["role"] = query["role"]

        if "email" in query:
            where_clauses.append("LOWER(email) = :email")
            params["email"] = query["email"].lower()

        if "phone" in query:
            where_clauses.append("phone = :phone")
            params["phone"] = query["phone"]

        if "referralCode" in query:
            where_clauses.append("UPPER(referral_code) = :referralCode")
            params["referralCode"] = query["referralCode"].upper()

        if "allowed_ids" in query:
            allowed_ids = query["allowed_ids"]
            if not allowed_ids:
                where_clauses.append("1=0")
            else:
                id_list = [int(aid) for aid in allowed_ids if str(aid).isdigit()]
                if not id_list:
                    where_clauses.append("1=0")
                else:
                    chunks = [id_list[i : i + 999] for i in range(0, len(id_list), 999)]
                    chunk_sqls = []
                    for chunk_idx, chunk in enumerate(chunks):
                        id_params = {f"aid_{chunk_idx}_{i}": aid for i, aid in enumerate(chunk)}
                        params.update(id_params)
                        id_placeholders = ", ".join([f":{k}" for k in id_params.keys()])
                        chunk_sqls.append(f"user_id IN ({id_placeholders})")

                    if len(chunk_sqls) == 1:
                        where_clauses.append(chunk_sqls[0])
                    else:
                        where_clauses.append("(" + " OR ".join(chunk_sqls) + ")")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return where_sql, params

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_sql, params = self._build_query_conditions(query or {})

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT user_id, external_id, user_id_formatted, name, email, password_hash,
                           role, phone, company_name, address, saved_addresses, is_active,
                           approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                           assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    ORDER BY user_id ASC
                    """
                ),
                params,
            )
            rows = result.fetchall()
        docs = [_row_to_dict(r) for r in rows]
        if query:
            filtered = []
            for doc in docs:
                match = True
                for k, v in query.items():
                    if k in ("allowed_ids",):
                        continue
                    if k in ("_id", "id"):
                        if doc.get("_id") != str(v) and doc.get("id") != v:
                            match = False
                            break
                    elif doc.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            return filtered
        return docs

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if set(query.keys()) == {"_id"} or set(query.keys()) == {"id"}:
            return await self.findById(query.get("_id") or query.get("id"))
        # Direct lookup for common fields to avoid full table scan
        if set(query.keys()) == {"email"} and query.get("email"):
            return await self.findByEmail(query["email"])
        if set(query.keys()) == {"phone"} and query.get("phone"):
            return await self.findByPhone(query["phone"])
        if set(query.keys()) == {"referralCode"} and query.get("referralCode"):
            return await self.findByReferralCode(query["referralCode"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT user_id, external_id, user_id_formatted, name, email, password_hash,
                           role, phone, company_name, address, saved_addresses, is_active,
                           approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                           assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    FROM {self.TABLE} WHERE user_id = :id
                    """
                ),
                {"id": int(id) if str(id).isdigit() else 0},
            )
            row = result.fetchone()
        return _row_to_dict(row) if row else None

    async def findByEmail(self, email: str) -> Optional[Dict]:
        """Direct SQL lookup by email — avoids full table scan."""
        factory = self._factory()
        if not factory or not email:
            return None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT user_id, external_id, user_id_formatted, name, email, password_hash,
                           role, phone, company_name, address, saved_addresses, is_active,
                           approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                           assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    FROM {self.TABLE} WHERE LOWER(email) = :email
                    FETCH FIRST 1 ROWS ONLY
                    """
                ),
                {"email": email.lower()},
            )
            row = result.fetchone()
        return _row_to_dict(row) if row else None

    async def findByPhone(self, phone: str) -> Optional[Dict]:
        """Direct SQL lookup by phone — avoids full table scan."""
        factory = self._factory()
        if not factory or not phone:
            return None
        # Normalize: strip non-digits
        normalized = "".join(filter(str.isdigit, phone))
        if not normalized:
            return None
        async with factory() as session:
            # Try exact match first, then normalized match
            result = await session.execute(
                text(
                    f"""
                    SELECT user_id, external_id, user_id_formatted, name, email, password_hash,
                           role, phone, company_name, address, saved_addresses, is_active,
                           approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                           assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    FROM {self.TABLE}
                    WHERE phone = :phone OR REGEXP_REPLACE(phone, '[^0-9]', '') = :normalized
                    FETCH FIRST 1 ROWS ONLY
                    """
                ),
                {"phone": phone, "normalized": normalized},
            )
            row = result.fetchone()
        return _row_to_dict(row) if row else None

    async def findByReferralCode(self, referral_code: str) -> Optional[Dict]:
        """Direct SQL lookup by referral_code — avoids full table scan."""
        factory = self._factory()
        if not factory or not referral_code:
            return None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT user_id, external_id, user_id_formatted, name, email, password_hash,
                           role, phone, company_name, address, saved_addresses, is_active,
                           approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                           assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    FROM {self.TABLE} WHERE UPPER(referral_code) = :referral_code
                    FETCH FIRST 1 ROWS ONLY
                    """
                ),
                {"referral_code": referral_code.upper()},
            )
            row = result.fetchone()
        return _row_to_dict(row) if row else None

    async def create(self, data: Dict) -> Dict:
        import json

        external_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)

        # Resolve userId / userIdFormatted from existing max
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        async with factory() as session:
            r = await session.execute(text(f"SELECT NVL(MAX(user_id), 0) + 1 AS next_id FROM {self.TABLE}"))
            next_id = r.scalar() or 1
        user_id_formatted = f"USER-{next_id}"

        address = data.get("address")
        saved_addresses = data.get("savedAddresses", [])
        if address and isinstance(address, dict) and address not in saved_addresses:
            saved_addresses = list(saved_addresses) + [address]
        address_json = json.dumps(address, default=str) if address else None
        saved_json = json.dumps(saved_addresses, default=str) if saved_addresses else None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id_formatted, name, email, password_hash,
                        role, phone, company_name, address, saved_addresses, is_active,
                        approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                        assigned_salesperson, is_email_verified, referral_code, created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id_formatted, :name, :email, :password_hash,
                        :role, :phone, :company_name, :address, :saved_addresses, :is_active,
                        :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,
                        :assigned_salesperson, :is_email_verified, :referral_code, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id_formatted": user_id_formatted,
                    "name": data.get("name") or "Customer",
                    "email": data.get("email"),
                    "password_hash": data.get("password"),
                    "role": data.get("role", "customer"),
                    "phone": data.get("phone") or None,
                    "company_name": data.get("companyName"),
                    "address": address_json,
                    "saved_addresses": saved_json,
                    "is_active": 1 if data.get("isActive", True) else 0,
                    "approval_status": data.get("approvalStatus", "approved"),
                    "is_deactivated": 1 if data.get("isDeactivated") else 0,
                    "credit_limit": data.get("creditLimit", 0),
                    "credit_used": data.get("creditUsed", 0),
                    "payment_terms": str(data.get("paymentTerms", "30")),
                    "assigned_salesperson": data.get("assignedSalesperson"),
                    "is_email_verified": 1 if data.get("isEmailVerified", False) else 0,
                    "referral_code": data.get("referralCode"),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()

            # Refetch to get the actual auto-increment ID
            result = await session.execute(
                text(f"SELECT user_id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
            )
            new_id = result.scalar()

        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        import json

        factory = self._factory()
        if not factory:
            return None
        existing = await self.findById(id)
        if not existing:
            return None
        now = datetime.now(timezone.utc)

        # Merge existing with update; only send changed columns to avoid CLOB overwrite
        merged = {**existing, **update_data}
        merged["updatedAt"] = now.isoformat()
        merged.pop("_id", None)
        merged.pop("createdAt", None)

        address = merged.get("address")
        saved_addresses = merged.get("savedAddresses", [])
        address_json = json.dumps(address, default=str) if address else None
        saved_json = json.dumps(saved_addresses, default=str) if saved_addresses else None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name, email = :email, password_hash = :password_hash,
                        role = :role, phone = :phone, company_name = :company_name,
                        address = :address, saved_addresses = :saved_addresses,
                        is_active = :is_active, approval_status = :approval_status,
                        is_deactivated = :is_deactivated, credit_limit = :credit_limit,
                        credit_used = :credit_used, payment_terms = :payment_terms,
                        assigned_salesperson = :assigned_salesperson,
                        is_email_verified = :is_email_verified, referral_code = :referral_code,
                        updated_at = :updated_at
                    WHERE user_id = :id
                    """
                ),
                {
                    "id": int(id) if str(id).isdigit() else 0,
                    "name": merged.get("name"),
                    "email": merged.get("email"),
                    "password_hash": merged.get("password"),
                    "role": merged.get("role"),
                    "phone": merged.get("phone") or None,
                    "company_name": merged.get("companyName"),
                    "address": address_json,
                    "saved_addresses": saved_json,
                    "is_active": 1 if merged.get("isActive", True) else 0,
                    "approval_status": merged.get("approvalStatus"),
                    "is_deactivated": 1 if merged.get("isDeactivated") else 0,
                    "credit_limit": merged.get("creditLimit", 0),
                    "credit_used": merged.get("creditUsed", 0),
                    "payment_terms": str(merged.get("paymentTerms"))
                    if merged.get("paymentTerms") is not None
                    else None,
                    "assigned_salesperson": merged.get("assignedSalesperson"),
                    "is_email_verified": 1 if merged.get("isEmailVerified", False) else 0,
                    "referral_code": merged.get("referralCode"),
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :id"),
                {"id": int(id) if str(id).isdigit() else 0},
            )
            await session.commit()
            return result.rowcount > 0

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    find_by_email = findByEmail
    find_by_phone = findByPhone
    find_by_referral_code = findByReferralCode
