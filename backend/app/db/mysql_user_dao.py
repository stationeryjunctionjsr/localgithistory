"""
MySQL DAO for sj_users (Fully Relational).
"""

import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings


def _row_to_doc(r, children: Dict) -> Dict:
    def clean_terms(t):
        if not t:
            return None
        t_str = str(t).replace("net_", "")
        return int(t_str) if t_str.isdigit() else None

    # Merge address & saved_addresses from children
    all_addresses = children.get("addresses", [])
    address = next((a for a in all_addresses if a.get("isPrimary")), {})
    saved_addresses = [a for a in all_addresses if not a.get("isPrimary")]

    seller_permissions = {
        "allowDeliverySlots": bool(getattr(r, "allow_delivery_slots", 0)),
        "allowUrgentDelivery": bool(getattr(r, "allow_urgent_delivery", 0)),
        "serviceablePincodes": children.get("serviceablePincodes", []),
        "urgentPincodes": children.get("urgentPincodes", []),
        "slotPincodes": children.get("slotPincodes", []),
    }

    is_seller_admin_val = getattr(r, "is_seller_admin", None)
    is_on_duty_val = getattr(r, "is_on_duty", None)
    commission_override_val = getattr(r, "commission_override_pct", None)

    return {
        "_id": str(r.id),
        "userId": r.id,
        "userIdFormatted": r.user_id_formatted or (f"USER-{r.id}" if r.id else None),
        "name": r.name,
        "email": r.email,
        "password": r.password_hash,
        "role": r.role,
        "phone": r.phone or "",
        "companyName": r.company_name,
        "address": address,
        "savedAddresses": saved_addresses,
        "isActive": bool(r.is_active) if r.is_active is not None else True,
        "approvalStatus": r.approval_status,
        "isDeactivated": bool(r.is_deactivated) if r.is_deactivated is not None else False,
        "creditLimit": float(r.credit_limit) if r.credit_limit is not None else 0,
        "creditUsed": float(r.credit_used) if r.credit_used is not None else 0,
        "paymentTerms": clean_terms(r.payment_terms),
        "assignedSalesperson": r.assigned_salesperson,
        "isEmailVerified": bool(r.is_email_verified) if r.is_email_verified is not None else False,
        "referralCode": r.referral_code,
        "isSellerAdmin": bool(is_seller_admin_val) if is_seller_admin_val is not None else False,
        "sellerPermissions": seller_permissions,
        "serviceAreaZones": children.get("zones", []),
        "isOnDuty": bool(is_on_duty_val) if is_on_duty_val is not None else False,
        "commissionOverridePct": float(commission_override_val) if commission_override_val is not None else None,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
    }


class MySQLUserDAO:
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
        if "isSellerAdmin" in query:
            where_clauses.append("is_seller_admin = :isSellerAdmin")
            params["isSellerAdmin"] = 1 if query["isSellerAdmin"] else 0
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
                        chunk_sqls.append(f"id IN ({id_placeholders})")
                    where_clauses.append("(" + " OR ".join(chunk_sqls) + ")" if len(chunk_sqls) > 1 else chunk_sqls[0])
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return where_sql, params

    async def _fetch_children(self, session, uids: List[int]) -> Dict[int, Dict]:
        children_map = {
            uid: {"addresses": [], "serviceablePincodes": [], "urgentPincodes": [], "slotPincodes": [], "zones": []}
            for uid in uids
        }
        if not uids:
            return children_map
        chunks = [uids[i : i + 999] for i in range(0, len(uids), 999)]
        for chunk in chunks:
            chunk_params = {f"uid_{i}": uid for i, uid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            # Addresses
            res = await session.execute(
                text(
                    f"SELECT user_id, is_primary, street, city, state, pincode, phone FROM sj_user_addresses WHERE user_id IN ({placeholders})"
                ),
                chunk_params,
            )
            for r in res.fetchall():
                children_map[r.user_id]["addresses"].append(
                    {
                        "isPrimary": bool(r.is_primary),
                        "street": r.street,
                        "city": r.city,
                        "state": r.state,
                        "pincode": r.pincode,
                        "phone": r.phone,
                    }
                )

            # Pincodes
            res = await session.execute(
                text(
                    f"SELECT user_id, pincode, pincode_type FROM sj_seller_pincodes WHERE user_id IN ({placeholders})"
                ),
                chunk_params,
            )
            for r in res.fetchall():
                if r.pincode_type == "serviceable":
                    children_map[r.user_id]["serviceablePincodes"].append(r.pincode)
                elif r.pincode_type == "urgent":
                    children_map[r.user_id]["urgentPincodes"].append(r.pincode)
                elif r.pincode_type == "slot":
                    children_map[r.user_id]["slotPincodes"].append(r.pincode)

            # Zones
            res = await session.execute(
                text(f"SELECT user_id, zone_name FROM sj_seller_zones WHERE user_id IN ({placeholders})"), chunk_params
            )
            for r in res.fetchall():
                children_map[r.user_id]["zones"].append(r.zone_name)
        return children_map

    async def _replace_children(self, session, uid: int, data: Dict):
        # Delete old
        await session.execute(text("DELETE FROM sj_user_addresses WHERE user_id = :uid"), {"uid": uid})
        await session.execute(text("DELETE FROM sj_seller_pincodes WHERE user_id = :uid"), {"uid": uid})
        await session.execute(text("DELETE FROM sj_seller_zones WHERE user_id = :uid"), {"uid": uid})

        # Insert Addresses
        address = data.get("address")
        saved_addresses = data.get("savedAddresses", [])
        if address and isinstance(address, dict):
            await session.execute(
                text(
                    "INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone) VALUES (:uid, 1, :st, :c, :s, :p, :ph)"
                ),
                {
                    "uid": uid,
                    "st": address.get("street"),
                    "c": address.get("city"),
                    "s": address.get("state"),
                    "p": address.get("pincode"),
                    "ph": address.get("phone"),
                },
            )
        for a in saved_addresses:
            if isinstance(a, dict) and a != address:
                await session.execute(
                    text(
                        "INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone) VALUES (:uid, 0, :st, :c, :s, :p, :ph)"
                    ),
                    {
                        "uid": uid,
                        "st": a.get("street"),
                        "c": a.get("city"),
                        "s": a.get("state"),
                        "p": a.get("pincode"),
                        "ph": a.get("phone"),
                    },
                )

        # Insert Permissions & Pincodes
        seller_perms = data.get("sellerPermissions", {})
        for p in seller_perms.get("serviceablePincodes", []):
            await session.execute(
                text(
                    "INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'serviceable')"
                ),
                {"uid": uid, "p": p},
            )
        for p in seller_perms.get("urgentPincodes", []):
            await session.execute(
                text("INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'urgent')"),
                {"uid": uid, "p": p},
            )
        for p in seller_perms.get("slotPincodes", []):
            await session.execute(
                text("INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'slot')"),
                {"uid": uid, "p": p},
            )

        # Insert Zones
        for z in data.get("serviceAreaZones", []):
            await session.execute(
                text("INSERT INTO sj_seller_zones (user_id, zone_name) VALUES (:uid, :z)"), {"uid": uid, "z": z}
            )

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        where_sql, params = self._build_query_conditions(query or {})
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"""
                SELECT id, external_id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,
                       created_at, updated_at
                FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC
            """),
                    params,
                )
            ).fetchall()
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])

        docs = [_row_to_doc(r, children_map[int(r.id)]) for r in rows]
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
        if set(query.keys()) in ({"_id"}, {"id"}):
            return await self.findById(query.get("_id") or query.get("id"))
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
            row = (
                await session.execute(
                    text(f"""
                SELECT id, external_id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,
                       created_at, updated_at
                FROM {self.TABLE} WHERE id = :id
            """),
                    {"id": int(id) if str(id).isdigit() else 0},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _row_to_doc(row, children_map[int(row.id)])

    async def findByEmail(self, email: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory or not email:
            return None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT id, external_id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,
                       created_at, updated_at
                FROM {self.TABLE} WHERE LOWER(email) = :email LIMIT 1
            """),
                    {"email": email.lower()},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _row_to_doc(row, children_map[int(row.id)])

    async def findByPhone(self, phone: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory or not phone:
            return None
        normalized = "".join(filter(str.isdigit, phone))
        if not normalized:
            return None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT id, external_id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,
                       created_at, updated_at
                FROM {self.TABLE} WHERE phone = :phone OR REGEXP_REPLACE(phone, '[^0-9]', '') = :normalized LIMIT 1
            """),
                    {"phone": phone, "normalized": normalized},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _row_to_doc(row, children_map[int(row.id)])

    async def findByReferralCode(self, referral_code: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory or not referral_code:
            return None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT id, external_id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct,
                       created_at, updated_at
                FROM {self.TABLE} WHERE UPPER(referral_code) = :referral_code LIMIT 1
            """),
                    {"referral_code": referral_code.upper()},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _row_to_doc(row, children_map[int(row.id)])

    async def create(self, data: Dict) -> Dict:
        external_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        async with factory() as session:
            next_id = (await session.execute(text(f"SELECT IFNULL(MAX(id), 0) + 1 FROM {self.TABLE}"))).scalar() or 1
            user_id_formatted = f"USER-{next_id}"

            await session.execute(
                text(f"""
                INSERT INTO {self.TABLE} (
                    external_id, user_id_formatted, name, email, password_hash, role, phone, company_name,
                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,
                    allow_delivery_slots, allow_urgent_delivery, is_on_duty, commission_override_pct, created_at, updated_at
                ) VALUES (
                    :external_id, :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name,
                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,
                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,
                    :allow_delivery_slots, :allow_urgent_delivery, :is_on_duty, :commission_override_pct, :created_at, :updated_at
                )
            """),
                {
                    "external_id": external_id,
                    "user_id_formatted": user_id_formatted,
                    "name": data.get("name") or "Customer",
                    "email": data.get("email"),
                    "password_hash": data.get("password"),
                    "role": data.get("role", "customer"),
                    "phone": data.get("phone") or None,
                    "company_name": data.get("companyName"),
                    "is_active": 1 if data.get("isActive", True) else 0,
                    "approval_status": data.get("approvalStatus", "approved"),
                    "is_deactivated": 1 if data.get("isDeactivated") else 0,
                    "credit_limit": data.get("creditLimit", 0),
                    "credit_used": data.get("creditUsed", 0),
                    "payment_terms": str(data.get("paymentTerms", "30")),
                    "assigned_salesperson": data.get("assignedSalesperson"),
                    "is_email_verified": 1 if data.get("isEmailVerified", False) else 0,
                    "referral_code": data.get("referralCode"),
                    "is_seller_admin": 1 if data.get("isSellerAdmin") else 0,
                    "allow_delivery_slots": 1 if data.get("sellerPermissions", {}).get("allowDeliverySlots") else 0,
                    "allow_urgent_delivery": 1 if data.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,
                    "is_on_duty": 1 if data.get("isOnDuty") else 0,
                    "commission_override_pct": data.get("commissionOverridePct"),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        now = datetime.now(timezone.utc)
        factory = self._factory()

        async with factory() as session:
            await session.execute(
                text(f"""
                UPDATE {self.TABLE} SET
                    name = :name, email = :email, password_hash = :password_hash, role = :role, phone = :phone,
                    company_name = :company_name, is_active = :is_active, approval_status = :approval_status,
                    is_deactivated = :is_deactivated, credit_limit = :credit_limit, credit_used = :credit_used,
                    payment_terms = :payment_terms, assigned_salesperson = :assigned_salesperson,
                    is_email_verified = :is_email_verified, referral_code = :referral_code, is_seller_admin = :is_seller_admin,
                    allow_delivery_slots = :allow_delivery_slots, allow_urgent_delivery = :allow_urgent_delivery,
                    is_on_duty = :is_on_duty, commission_override_pct = :commission_override_pct, updated_at = :updated_at
                WHERE id = :id
            """),
                {
                    "id": int(id) if str(id).isdigit() else 0,
                    "name": merged.get("name"),
                    "email": merged.get("email"),
                    "password_hash": merged.get("password"),
                    "role": merged.get("role"),
                    "phone": merged.get("phone") or None,
                    "company_name": merged.get("companyName"),
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
                    "is_seller_admin": 1 if merged.get("isSellerAdmin") else 0,
                    "allow_delivery_slots": 1 if merged.get("sellerPermissions", {}).get("allowDeliverySlots") else 0,
                    "allow_urgent_delivery": 1 if merged.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,
                    "is_on_duty": 1 if merged.get("isOnDuty") else 0,
                    "commission_override_pct": merged.get("commissionOverridePct"),
                    "updated_at": now,
                },
            )
            await self._replace_children(session, int(id) if str(id).isdigit() else 0, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else 0}
            )
            await session.commit()
            return result.rowcount > 0

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    find_by_email = findByEmail
    find_by_phone = findByPhone
    find_by_referral_code = findByReferralCode
