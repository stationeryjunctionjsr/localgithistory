from typing import Any
from app.models.schemas import UserInternalCreate, UserInternalUpdate, AddressSnippet
from app.models.user import User, UserFilter
"""
MySQL DAO for sj_users (Fully Relational).
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.config.settings import settings

from app.models.base import CamelBaseModel
from pydantic import Field


class UserAddressItem(CamelBaseModel):
    user_id: int
    address: AddressSnippet


class UserZoneItem(CamelBaseModel):
    user_id: int
    zone_id: int


class UserChildrenBatch(CamelBaseModel):
    addresses: list[UserAddressItem] = Field(default_factory=list)
    zones: list[UserZoneItem] = Field(default_factory=list)


def _map_to_schema(
    r,
    addresses: Optional[list[AddressSnippet]] = None,
    zones: Optional[list[int]] = None,
) -> User:
    u = User.model_validate(r)
    all_addresses = addresses or []
    u.address = next((a for a in all_addresses if a.is_primary), None)
    u.saved_addresses = [a for a in all_addresses if not a.is_primary]
    u.service_area_zones = zones or []
    
    if not u.user_id_formatted and u.id:
        u.user_id_formatted = f"USER-{r.id}"
    
    u.password = r.password_hash
        
    return u


class UserRoleCounts(CamelBaseModel):
    customer: int = 0
    wholesaler: int = 0
    valet: int = 0
    seller: int = 0
    admin: int = 0
    super_admin: int = 0


class MySQLUserDAO:

    @property
    def TABLE(self):
        return 'sj_users'

    def _build_query_conditions(self, filter_params: Optional[UserFilter] = None) -> tuple[str, dict]:
        where_clauses = []
        params = {}
        if not filter_params:
            return "1=1", {}

        if filter_params.role is not None:
            where_clauses.append('role = :role')
            params['role'] = filter_params.role
        if filter_params.email is not None:
            where_clauses.append('LOWER(email) = :email')
            params['email'] = filter_params.email.lower()
        if filter_params.phone is not None:
            where_clauses.append('phone = :phone')
            params['phone'] = filter_params.phone
        if filter_params.referral_code is not None:
            where_clauses.append('UPPER(referral_code) = :referral_code')
            params['referral_code'] = filter_params.referral_code.upper()
        if filter_params.is_seller_admin is not None:
            where_clauses.append('is_seller_admin = :is_seller_admin')
            params['is_seller_admin'] = 1 if filter_params.is_seller_admin else 0
        if filter_params.is_on_duty is not None:
            where_clauses.append('is_on_duty = :is_on_duty')
            params['is_on_duty'] = 1 if filter_params.is_on_duty else 0
        if filter_params.approval_status is not None:
            where_clauses.append('approval_status = :approval_status')
            params['approval_status'] = filter_params.approval_status
        if filter_params.is_active is not None:
            where_clauses.append('is_active = :is_active')
            params['is_active'] = 1 if filter_params.is_active else 0
        if filter_params.allowed_ids is not None:
            id_list = [aid for aid in filter_params.allowed_ids if aid is not None]
            if not id_list:
                where_clauses.append('1=0')
            else:
                chunks = [id_list[i:i + 999] for i in range(0, len(id_list), 999)]
                conds = []
                for chunk_idx, chunk in enumerate(chunks):
                    id_params = {f'aid_{chunk_idx}_{i}': aid for i, aid in enumerate(chunk)}
                    params.update(id_params)
                    id_placeholders = ', '.join([f':{k}' for k in id_params.keys()])
                    conds.append(f'id IN ({id_placeholders})')
                where_clauses.append('(' + ' OR '.join(conds) + ')')

        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        return (where_sql, params)

    async def _fetch_children(
        self, session, uids: list[int]
    ) -> UserChildrenBatch:
        if not uids:
            return UserChildrenBatch()
        chunks = [uids[i:i + 999] for i in range(0, len(uids), 999)]
        addr_items: list[UserAddressItem] = []
        zone_items: list[UserZoneItem] = []
        for chunk in chunks:
            chunk_params = {f'uid_{i}': uid for i, uid in enumerate(chunk)}
            placeholders = ', '.join([f':{k}' for k in chunk_params.keys()])
            res = await session.execute(text(f'SELECT user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code FROM sj_user_addresses WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                addr_items.append(
                    UserAddressItem(
                        user_id=r.user_id,
                        address=AddressSnippet(
                            is_primary=bool(r.is_primary),
                            street=r.street,
                            city=r.city,
                            state=r.state,
                            pincode=r.pincode,
                            phone=r.phone,
                            district=r.district,
                            country=r.country,
                            google_location=r.google_location,
                            latitude=float(r.latitude) if r.latitude is not None else None,
                            longitude=float(r.longitude) if r.longitude is not None else None,
                            address=r.address_text,
                            zip_code=r.zip_code,
                        ),
                    )
                )
            res = await session.execute(text(f'SELECT user_id, zone_name, zone_id FROM sj_seller_zones WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                if r.zone_id is not None:
                    zone_items.append(UserZoneItem(user_id=r.user_id, zone_id=r.zone_id))
        return UserChildrenBatch(addresses=addr_items, zones=zone_items)

    async def _replace_children(self, session, uid: int, data: User):
        await session.execute(text('DELETE FROM sj_user_addresses WHERE user_id = :uid'), {'uid': uid})
        await session.execute(text('DELETE FROM sj_seller_zones WHERE user_id = :uid'), {'uid': uid})
        address = data.address
        saved_addresses = data.saved_addresses if data.saved_addresses is not None else []
        if address:
            params = {
                'uid': uid,
                'st': address.street,
                'c': address.city,
                's': address.state,
                'p': address.pincode,
                'ph': address.phone,
                'd': address.district,
                'co': address.country,
                'gl': address.google_location,
                'lat': address.latitude,
                'lon': address.longitude,
                'at': address.address,
                'zc': address.zip_code,
            }
            await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 1, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), params)
        for a in saved_addresses:
            if a != address:
                a_params = {
                    'uid': uid,
                    'st': a.street,
                    'c': a.city,
                    's': a.state,
                    'p': a.pincode,
                    'ph': a.phone,
                    'd': a.district,
                    'co': a.country,
                    'gl': a.google_location,
                    'lat': a.latitude,
                    'lon': a.longitude,
                    'at': a.address,
                    'zc': a.zip_code,
                }
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 0, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), a_params)
        for zone_id in data.service_area_zones if data.service_area_zones is not None else []:
            if zone_id is None:
                continue
            name_res = await session.execute(text('SELECT name FROM sj_delivery_zones WHERE id = :zid LIMIT 1'), {'zid': zone_id})
            name_row = name_res.fetchone()
            zone_name = name_row.name if name_row else str(zone_id)
            await session.execute(text('INSERT INTO sj_seller_zones (user_id, zone_name, zone_id) VALUES (:uid, :zn, :zi)'), {'uid': uid, 'zn': zone_name, 'zi': zone_id})

    async def findAll(self, filter_params: Optional[UserFilter] = None, skip: Optional[int] = None, limit: Optional[int] = None) -> list[User]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        where_sql, params = self._build_query_conditions(filter_params)
        async with async_session() as session:
            try:
                query_str = f'\n                SELECT id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC\n            '
                if limit is not None:
                    query_str += f' LIMIT {limit}'
                if skip is not None:
                    query_str += f' OFFSET {skip}'
                rows = (await session.execute(text(query_str), params)).fetchall()
                children = await self._fetch_children(session, [r.id for r in rows])
            except Exception as e:
                await session.rollback()
                raise e
        return [
            _map_to_schema(
                r,
                addresses=[ai.address for ai in children.addresses if ai.user_id == r.id],
                zones=[zi.zone_id for zi in children.zones if zi.user_id == r.id],
            )
            for r in rows
        ]

    async def findSuperAdmin(self) -> Optional[User]:
        records = await self.findAll(UserFilter(role="super_admin"), limit=1)
        return records[0] if records else None

    async def findOne(self, filter_params: UserFilter) -> Optional[User]:
        records = await self.findAll(filter_params, limit=1)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[User]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            try:
                row = (await session.execute(text(f"""
                SELECT id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, gst_number, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,
                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                       created_at, updated_at
                FROM {self.TABLE} WHERE id = :id LIMIT 1
            """), {'id': id})).fetchone()
                if not row:
                    return None
                children = await self._fetch_children(session, [row.id])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(
            row,
            addresses=[ai.address for ai in children.addresses if ai.user_id == row.id],
            zones=[zi.zone_id for zi in children.zones if zi.user_id == row.id],
        )

    async def findByIds(self, ids: list[int]) -> list[User]:
        if not ids:
            return []
        async_session = get_async_session_factory()
        if not async_session:
            return []
        placeholders = [f":id_{idx}" for idx in range(len(ids))]
        params = {f"id_{idx}": val for idx, val in enumerate(ids)}
        where_sql = f"id IN ({', '.join(placeholders)})"
        async with async_session() as session:
            try:
                rows = (
                    await session.execute(
                        text(
                            f"""
                        SELECT id, user_id_formatted, name, email, password_hash,
                               role, phone, company_name, gst_number, is_active,
                               approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                               assigned_salesperson, is_email_verified, referral_code,
                               is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,
                               bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                               created_at, updated_at
                        FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC
                    """
                        ),
                        params,
                    )
                ).fetchall()
                if not rows:
                    return []
                children = await self._fetch_children(session, [r.id for r in rows])
                return [
                    _map_to_schema(
                        r,
                        addresses=[ai.address for ai in children.addresses if ai.user_id == r.id],
                        zones=[zi.zone_id for zi in children.zones if zi.user_id == r.id],
                    )
                    for r in rows
                ]
            except Exception:
                await session.rollback()
                raise

    async def get_user_counts_by_role(self) -> UserRoleCounts:
        """Returns UserRoleCounts via direct SQL pushdown without loading user rows."""
        async_session = get_async_session_factory()
        if not async_session:
            return UserRoleCounts()
        async with async_session() as session:
            q = text(f"""
                SELECT 
                    COUNT(CASE WHEN role = 'customer' THEN 1 END) AS customer,
                    COUNT(CASE WHEN role = 'wholesaler' THEN 1 END) AS wholesaler,
                    COUNT(CASE WHEN role = 'valet' THEN 1 END) AS valet,
                    COUNT(CASE WHEN role = 'seller' THEN 1 END) AS seller,
                    COUNT(CASE WHEN role = 'admin' THEN 1 END) AS admin,
                    COUNT(CASE WHEN role = 'super_admin' THEN 1 END) AS super_admin
                FROM {self.TABLE}
            """)
            r = (await session.execute(q)).fetchone()
            if not r:
                return UserRoleCounts()
            return UserRoleCounts(
                customer=r.customer or 0,
                wholesaler=r.wholesaler or 0,
                valet=r.valet or 0,
                seller=r.seller or 0,
                admin=r.admin or 0,
                super_admin=r.super_admin or 0,
            )

    async def findByEmail(self, email: str) -> Optional[User]:
        if not email:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            try:
                row = (await session.execute(text(f"""
                SELECT id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, gst_number, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,
                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                       created_at, updated_at
                FROM {self.TABLE} WHERE LOWER(email) = :email LIMIT 1
            """), {'email': email.lower()})).fetchone()
                if not row:
                    return None
                children = await self._fetch_children(session, [row.id])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(
            row,
            addresses=[ai.address for ai in children.addresses if ai.user_id == row.id],
            zones=[zi.zone_id for zi in children.zones if zi.user_id == row.id],
        )

    async def findByPhone(self, phone: str) -> Optional[User]:
        if not phone:
            return None
        normalized = ''.join(filter(str.isdigit, phone))
        if not normalized:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            try:
                row = (await session.execute(text(f"""
                SELECT id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, gst_number, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,
                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                       created_at, updated_at
                FROM {self.TABLE} WHERE phone = :phone OR REGEXP_REPLACE(phone, '[^0-9]', '') = :normalized LIMIT 1
            """), {'phone': phone, 'normalized': normalized})).fetchone()
                if not row:
                    return None
                children = await self._fetch_children(session, [row.id])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(
            row,
            addresses=[ai.address for ai in children.addresses if ai.user_id == row.id],
            zones=[zi.zone_id for zi in children.zones if zi.user_id == row.id],
        )

    async def findByReferralCode(self, referral_code: str) -> Optional[User]:
        if not referral_code:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            try:
                row = (await session.execute(text(f"""
                SELECT id, user_id_formatted, name, email, password_hash,
                       role, phone, company_name, gst_number, is_active,
                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                       assigned_salesperson, is_email_verified, referral_code,
                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,
                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                       created_at, updated_at
                FROM {self.TABLE} WHERE UPPER(referral_code) = :referral_code LIMIT 1
            """), {'referral_code': referral_code.upper()})).fetchone()
                if not row:
                    return None
                children = await self._fetch_children(session, [row.id])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(
            row,
            addresses=[ai.address for ai in children.addresses if ai.user_id == row.id],
            zones=[zi.zone_id for zi in children.zones if zi.user_id == row.id],
        )

    async def getNextUserId(self) -> int:
        async_session = get_async_session_factory()
        if not async_session:
            return 1
        async with async_session() as session:
            val = (await session.execute(text(f"SELECT IFNULL(MAX(id), 0) + 1 FROM {self.TABLE}"))).scalar()
            return val or 1

    async def create(self, data: UserInternalCreate) -> User:
        now = datetime.now(timezone.utc)
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError('MySQL not configured')
        async with async_session() as session:
            try:
                next_id = (await session.execute(text(f'SELECT IFNULL(MAX(id), 0) + 1 FROM {self.TABLE}'))).scalar() or 1
                user_id_formatted = f'USER-{next_id}'
                result = await session.execute(text(f"""
                INSERT INTO {self.TABLE} (
                    user_id_formatted, name, email, password_hash, role, phone, company_name, gst_number,
                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,
                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,
                    is_on_duty, commission_override_pct, upi_id, qr_code_url,
                    bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,
                    created_at, updated_at
                ) VALUES (
                    :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name, :gst_number,
                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,
                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,
                    :is_on_duty, :commission_override_pct, :upi_id, :qr_code_url,
                    :bank_account_number, :bank_ifsc_code, :bank_account_holder, :bank_name,
                    :created_at, :updated_at
                )
            """), {'user_id_formatted': user_id_formatted, 'name': data.name or 'Customer', 'email': data.email, 'password_hash': data.password, 'role': data.role if data.role is not None else 'customer', 'phone': data.phone or None, 'company_name': data.company_name, 'gst_number': data.gstin, 'is_active': 1 if (data.is_active if data.is_active is not None else True) else 0, 'approval_status': data.approval_status if data.approval_status is not None else 'approved', 'is_deactivated': 1 if data.is_deactivated else 0, 'credit_limit': data.credit_limit if data.credit_limit is not None else 0, 'credit_used': data.credit_used if data.credit_used is not None else 0, 'payment_terms': data.payment_terms if data.payment_terms is not None else 30, 'assigned_salesperson': data.assigned_salesperson, 'is_email_verified': 1 if (data.is_email_verified if data.is_email_verified is not None else False) else 0, 'referral_code': data.referral_code, 'is_seller_admin': 1 if data.is_seller_admin else 0, 'is_on_duty': 1 if data.is_on_duty else 0, 'commission_override_pct': data.commission_override_pct, 'upi_id': data.upi_id, 'qr_code_url': data.qr_code_url, 'bank_account_number': data.bank_account_number, 'bank_ifsc_code': data.bank_ifsc_code, 'bank_account_holder': data.bank_account_holder, 'bank_name': data.bank_name, 'created_at': now, 'updated_at': now})
                new_id = result.lastrowid
                temp_user = User(
                    id=new_id,
                    user_id_formatted=user_id_formatted,
                    name=data.name,
                    email=data.email,
                    password=data.password,
                    role=data.role,
                    phone=data.phone,
                    company_name=data.company_name,
                    gst_number=data.gstin,
                    address=data.address,
                    saved_addresses=data.saved_addresses if data.saved_addresses else [],
                    is_active=data.is_active if data.is_active is not None else True,
                    approval_status=data.approval_status if data.approval_status is not None else 'approved',
                    is_deactivated=data.is_deactivated if data.is_deactivated is not None else False,
                    credit_limit=data.credit_limit if data.credit_limit is not None else 0.0,
                    credit_used=data.credit_used if data.credit_used is not None else 0.0,
                    payment_terms=data.payment_terms,
                    assigned_salesperson=data.assigned_salesperson,
                    is_email_verified=data.is_email_verified if data.is_email_verified is not None else False,
                    referral_code=data.referral_code,
                    is_seller_admin=data.is_seller_admin if data.is_seller_admin is not None else False,
                    service_area_zones=data.service_area_zones if data.service_area_zones else [],
                    is_on_duty=data.is_on_duty if data.is_on_duty is not None else False,
                    commission_override_pct=data.commission_override_pct,
                    upi_id=data.upi_id,
                    qr_code_url=data.qr_code_url,
                    bank_account_number=data.bank_account_number,
                    bank_ifsc_code=data.bank_ifsc_code,
                    bank_account_holder=data.bank_account_holder,
                    bank_name=data.bank_name,
                    created_at=now,
                    updated_at=now
                )
                await self._replace_children(session, new_id, temp_user)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
        return await self.findById(new_id)

    async def add_credit_used_atomic(self, id: int, amount: float) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        from sqlalchemy import text
        async with async_session() as session:
            try:
                res = await session.execute(text(f"""
                    UPDATE {self.TABLE} 
                    SET credit_used = COALESCE(credit_used, 0) + :amount,
                        updated_at = UTC_TIMESTAMP()
                    WHERE id = :uid 
                    AND (credit_limit IS NULL OR credit_limit = 0 OR COALESCE(credit_used, 0) + :amount <= credit_limit)
                """), {'uid': id, 'amount': amount})
                await session.commit()
                return res.rowcount > 0


            except Exception as e:
                await session.rollback()
                raise e
    async def update(self, id: int, update_data: 'UserInternalUpdate') -> Optional[User]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        now = datetime.now(timezone.utc)
        async_session = get_async_session_factory()
        if not async_session:
            return None
        
        # Manually extract fields from the Pydantic update_data model, falling back to existing dict
        name = update_data.name if update_data.name is not None else existing.name
        email = update_data.email if update_data.email is not None else existing.email
        password_hash = update_data.password if update_data.password is not None else existing.password
        role = update_data.role if update_data.role is not None else existing.role
        phone = update_data.phone if update_data.phone is not None else existing.phone
        company_name = update_data.company_name if update_data.company_name is not None else existing.company_name
        is_active = update_data.is_active if update_data.is_active is not None else existing.is_active
        approval_status = update_data.approval_status if update_data.approval_status is not None else existing.approval_status
        gst_number = update_data.gstin if update_data.gstin is not None else None
        is_deactivated = update_data.is_deactivated if update_data.is_deactivated is not None else existing.is_deactivated
        credit_limit = update_data.credit_limit if update_data.credit_limit is not None else existing.credit_limit
        credit_used = update_data.credit_used if update_data.credit_used is not None else existing.credit_used
        payment_terms = update_data.payment_terms if update_data.payment_terms is not None else existing.payment_terms
        assigned_salesperson = update_data.assigned_salesperson if update_data.assigned_salesperson is not None else existing.assigned_salesperson
        is_email_verified = update_data.is_email_verified if update_data.is_email_verified is not None else existing.is_email_verified
        referral_code = update_data.referral_code if update_data.referral_code is not None else existing.referral_code
        is_seller_admin = update_data.is_seller_admin if update_data.is_seller_admin is not None else existing.is_seller_admin
        is_on_duty = update_data.is_on_duty if update_data.is_on_duty is not None else existing.is_on_duty
        commission_override_pct = update_data.commission_override_pct if update_data.commission_override_pct is not None else existing.commission_override_pct
        upi_id = update_data.upi_id if update_data.upi_id is not None else existing.upi_id
        qr_code_url = update_data.qr_code_url if update_data.qr_code_url is not None else existing.qr_code_url
        bank_account_number = update_data.bank_account_number if update_data.bank_account_number is not None else existing.bank_account_number
        bank_ifsc_code = update_data.bank_ifsc_code if update_data.bank_ifsc_code is not None else existing.bank_ifsc_code
        bank_account_holder = update_data.bank_account_holder if update_data.bank_account_holder is not None else existing.bank_account_holder
        bank_name = update_data.bank_name if update_data.bank_name is not None else existing.bank_name
        async with async_session() as session:
            try:
                await session.execute(text('''
                    UPDATE sj_users SET
                        name = :name, email = :email, password_hash = :password_hash, role = :role, phone = :phone,
                        company_name = :company_name, gst_number = :gst_number, is_active = :is_active, approval_status = :approval_status,
                        is_deactivated = :is_deactivated, credit_limit = :credit_limit, credit_used = :credit_used,
                        payment_terms = :payment_terms, assigned_salesperson = :assigned_salesperson,
                        is_email_verified = :is_email_verified, referral_code = :referral_code, is_seller_admin = :is_seller_admin,
                        is_on_duty = :is_on_duty, commission_override_pct = :commission_override_pct,
                        upi_id = :upi_id, qr_code_url = :qr_code_url,
                        bank_account_number = :bank_account_number, bank_ifsc_code = :bank_ifsc_code,
                        bank_account_holder = :bank_account_holder, bank_name = :bank_name,
                        updated_at = :updated_at
                    WHERE id = :id_int
                '''), {
                    'id_int': existing.id,
                    'name': name,
                    'email': email,
                    'password_hash': password_hash,
                    'role': role,
                    'phone': phone or None,
                    'company_name': company_name,
                    'gst_number': gst_number,
                    'is_active': 1 if (is_active if is_active is not None else True) else 0,
                    'approval_status': approval_status,
                    'is_deactivated': 1 if is_deactivated else 0,
                    'credit_limit': credit_limit if credit_limit is not None else 0,
                    'credit_used': credit_used if credit_used is not None else 0,
                    'payment_terms': payment_terms,
                    'assigned_salesperson': assigned_salesperson,
                    'is_email_verified': 1 if is_email_verified else 0,
                    'referral_code': referral_code,
                    'is_seller_admin': 1 if is_seller_admin else 0,
                    'is_on_duty': 1 if is_on_duty else 0,
                    'commission_override_pct': commission_override_pct,
                    'upi_id': upi_id,
                    'qr_code_url': qr_code_url,
                    'bank_account_number': bank_account_number,
                    'bank_ifsc_code': bank_ifsc_code,
                    'bank_account_holder': bank_account_holder,
                    'bank_name': bank_name,
                    'updated_at': now
                })
            
                child_keys = ['address', 'saved_addresses', 'service_area_zones']
                has_child_updates = False
                for k in child_keys:
                    if k in update_data.model_fields_set:
                        has_child_updates = True
                        
                if has_child_updates:
                    fields_set = update_data.model_fields_set
                    if "address" in fields_set:
                        existing.address = update_data.address
                    if "saved_addresses" in fields_set:
                        existing.saved_addresses = update_data.saved_addresses
                    if "service_area_zones" in fields_set:
                        existing.service_area_zones = update_data.service_area_zones
                            
                    await self._replace_children(session, existing.id, existing)
                
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
        return await self.findById(id)
    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            try:
                result = await session.execute(text(f'DELETE FROM {self.TABLE} WHERE id = :id'), {'id': id})
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                raise e
    find_all = findAll
    find_by_id = findById
    find_one = findOne
    find_by_email = findByEmail
    find_by_phone = findByPhone
    find_by_referral_code = findByReferralCode
