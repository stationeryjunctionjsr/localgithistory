from typing import Any
from app.models.schemas import UserInternalCreate, UserInternalUpdate, UserResponse
from app.models.user import User
'\nMySQL DAO for sj_users (Fully Relational).\n'
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.config.settings import settings

def _map_to_schema(r, children: Dict) -> User:
    d = dict(r._mapping)
    all_addresses = children.get('addresses', [])
    d['address'] = next((a for a in all_addresses if a.get('isPrimary')), None)
    d['saved_addresses'] = [a for a in all_addresses if not a.get('isPrimary')]
    d['service_area_zones'] = children.get('zones', [])
    
    d['user_id'] = d.get('id')
    if not d.get('user_id_formatted'):
        d['user_id_formatted'] = f'USER-{d["id"]}' if d.get('id') else None
    
    d['password'] = d.pop('password_hash', None)
    d['gst_number'] = d.pop('gst_number', None)

    # Convert payment_terms string net_30 to int
    pt = d.get('payment_terms')
    if pt:
        pt_str = str(pt).replace('net_', '')
        d['payment_terms'] = int(pt_str) if pt_str.isdigit() else None
        
    return User.model_validate(d)

class MySQLUserDAO:

    @property
    def TABLE(self):
        return 'sj_users'

    def _factory(self):
        return get_async_session_factory()

    def _build_query_conditions(self, query: Dict) -> tuple[str, Dict]:
        where_clauses = []
        params = {}
        if 'role' in query:
            where_clauses.append('role = :role')
            params['role'] = query['role']
        if 'email' in query:
            where_clauses.append('LOWER(email) = :email')
            params['email'] = query['email'].lower()
        if 'phone' in query:
            where_clauses.append('phone = :phone')
            params['phone'] = query['phone']
        if 'referral_code' in query:
            where_clauses.append('UPPER(referral_code) = :referralCode')
            params['referral_code'] = query['referral_code'].upper()
        if 'is_seller_admin' in query:
            where_clauses.append('is_seller_admin = :isSellerAdmin')
            params['is_seller_admin'] = 1 if query['is_seller_admin'] else 0
        if 'is_on_duty' in query:
            where_clauses.append('is_on_duty = :isOnDuty')
            params['is_on_duty'] = 1 if query['is_on_duty'] else 0
        if 'approvalStatus' in query:
            where_clauses.append('approval_status = :approvalStatus')
            params['approvalStatus'] = query['approvalStatus']
        if 'isActive' in query:
            where_clauses.append('is_active = :isActive')
            params['isActive'] = 1 if query['isActive'] else 0
        if 'allowed_ids' in query:
            allowed_ids = query['allowed_ids']
            if not allowed_ids:
                where_clauses.append('1=0')
            else:
                id_list = [int(aid) for aid in allowed_ids if str(aid).isdigit()]
                if not id_list:
                    where_clauses.append('1=0')
                else:
                    chunks = [id_list[i:i + 999] for i in range(0, len(id_list), 999)]
                    chunk_sqls = []
                    for chunk_idx, chunk in enumerate(chunks):
                        id_params = {f'aid_{chunk_idx}_{i}': aid for i, aid in enumerate(chunk)}
                        params.update(id_params)
                        id_placeholders = ', '.join([f':{k}' for k in id_params.keys()])
                        chunk_sqls.append(f'id IN ({id_placeholders})')
                    where_clauses.append('(' + ' OR '.join(chunk_sqls) + ')' if len(chunk_sqls) > 1 else chunk_sqls[0])
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        return (where_sql, params)

    async def _fetch_children(self, session, uids: List[int]) -> Dict[int, Dict]:
        children_map = {uid: {'addresses': [], 'zones': []} for uid in uids}
        if not uids:
            return children_map
        chunks = [uids[i:i + 999] for i in range(0, len(uids), 999)]
        for chunk in chunks:
            chunk_params = {f'uid_{i}': uid for i, uid in enumerate(chunk)}
            placeholders = ', '.join([f':{k}' for k in chunk_params.keys()])
            res = await session.execute(text(f'SELECT user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code FROM sj_user_addresses WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                children_map[r.user_id]['addresses'].append({'isPrimary': bool(r.is_primary), 'street': r.street, 'city': r.city, 'state': r.state, 'pincode': r.pincode, 'phone': r.phone, 'district': r.district, 'country': r.country, 'googleLocation': r.google_location, 'latitude': float(r.latitude) if r.latitude is not None else None, 'longitude': float(r.longitude) if r.longitude is not None else None})
            res = await session.execute(text(f'SELECT user_id, zone_name, zone_id FROM sj_seller_zones WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                children_map[r.user_id]['zones'].append(r.zone_name)
        return children_map

    async def _replace_children(self, session, uid: int, data: User):
        await session.execute(text('DELETE FROM sj_user_addresses WHERE user_id = :uid'), {'uid': uid})
        await session.execute(text('DELETE FROM sj_seller_zones WHERE user_id = :uid'), {'uid': uid})
        address = data.address
        saved_addresses = data.saved_addresses if data.saved_addresses is not None else []
        if address:
            params = {'uid': uid, 'st': getattr(address, 'street', None), 'c': getattr(address, 'city', None), 's': getattr(address, 'state', None), 'p': getattr(address, 'pincode', None), 'ph': getattr(address, 'phone', None), 'd': getattr(address, 'district', None), 'co': getattr(address, 'country', None), 'gl': getattr(address, 'googleLocation', None), 'lat': getattr(address, 'latitude', None), 'lon': getattr(address, 'longitude', None), 'at': getattr(address, 'address', None), 'zc': getattr(address, 'zipCode', None)}
            try:
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 1, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), params)
            except Exception as e:
                import traceback
                print("CRASH ON ADDRESS PARAMS:", params)
                traceback.print_exc()
                raise e
        for a in saved_addresses:
            if a != address:
                a_params = {'uid': uid, 'st': getattr(a, 'street', None), 'c': getattr(a, 'city', None), 's': getattr(a, 'state', None), 'p': getattr(a, 'pincode', None), 'ph': getattr(a, 'phone', None), 'd': getattr(a, 'district', None), 'co': getattr(a, 'country', None), 'gl': getattr(a, 'googleLocation', None), 'lat': getattr(a, 'latitude', None), 'lon': getattr(a, 'longitude', None), 'at': getattr(a, 'address', None), 'zc': getattr(a, 'zipCode', None)}
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone, district, country, google_location, latitude, longitude, address_text, zip_code) VALUES (:uid, 0, :st, :c, :s, :p, :ph, :d, :co, :gl, :lat, :lon, :at, :zc)'), a_params)
        for zone_ext_id in data.service_area_zones if data.service_area_zones is not None else []:
            name_res = await session.execute(text('SELECT name FROM sj_delivery_zones WHERE external_id = :eid LIMIT 1'), {'eid': zone_ext_id})
            name_row = name_res.fetchone()
            zone_name = name_row.name if name_row else zone_ext_id
            await session.execute(text('INSERT INTO sj_seller_zones (user_id, zone_name, zone_id) VALUES (:uid, :zn, :zi)'), {'uid': uid, 'zn': zone_name, 'zi': zone_ext_id})

    async def findAll(self, query: Optional[Dict]=None, skip: Optional[int]=None, limit: Optional[int]=None) -> List[User]:
        factory = self._factory()
        if not factory:
            return []
        where_sql, params = self._build_query_conditions(query or {})
        async with factory() as session:
            try:
                query_str = f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC\n            '
                if limit is not None:
                    query_str += f' LIMIT {int(limit)}'
                if skip is not None:
                    query_str += f' OFFSET {int(skip)}'
                rows = (await session.execute(text(query_str), params)).fetchall()
                children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            except Exception as e:
                await session.rollback()
                raise e
        from app.models.user import User
        docs = [UserResponse.model_validate(_map_to_schema(r, children_map[int(r.id)] if int(r.id) in children_map else {})) for r in rows]
        pass
        return docs

    async def findOne(self, query: Dict) -> Optional[User]:
        if set(query.keys()) in ({'_id'}, {'id'}):
            return await self.findById((query['_id'] if '_id' in query else None) or (query['id'] if 'id' in query else None))
        if set(query.keys()) == {'email'} and (query['email'] if 'email' in query else None):
            return await self.findByEmail(query['email'])
        if set(query.keys()) == {'phone'} and (query['phone'] if 'phone' in query else None):
            return await self.findByPhone(query['phone'])
        if set(query.keys()) == {'referral_code'} and (query['referral_code'] if 'referral_code' in query else None):
            return await self.findByReferralCode(query['referral_code'])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[User]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            try:
                row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE id = :id\n            '), {'id': int(id) if str(id).isdigit() else None})).fetchone()
                if not row:
                    return None
                children_map = await self._fetch_children(session, [int(row.id)])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByEmail(self, email: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not email:
            return None
        async with factory() as session:
            try:
                row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE LOWER(email) = :email LIMIT 1\n            '), {'email': email.lower()})).fetchone()
                if not row:
                    return None
                children_map = await self._fetch_children(session, [int(row.id)])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByPhone(self, phone: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not phone:
            return None
        normalized = ''.join(filter(str.isdigit, phone))
        if not normalized:
            return None
        async with factory() as session:
            try:
                row = (await session.execute(text(f"\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE phone = :phone OR REGEXP_REPLACE(phone, '[^0-9]', '') = :normalized LIMIT 1\n            "), {'phone': phone, 'normalized': normalized})).fetchone()
                if not row:
                    return None
                children_map = await self._fetch_children(session, [int(row.id)])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByReferralCode(self, referral_code: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not referral_code:
            return None
        async with factory() as session:
            try:
                row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, gst_number, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE UPPER(referral_code) = :referral_code LIMIT 1\n            '), {'referral_code': referral_code.upper()})).fetchone()
                if not row:
                    return None
                children_map = await self._fetch_children(session, [int(row.id)])
            except Exception as e:
                await session.rollback()
                raise e
        return _map_to_schema(row, children_map[int(row.id)])

    async def create(self, data: UserInternalCreate) -> User:
        external_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        factory = self._factory()
        if not factory:
            raise RuntimeError('MySQL not configured')
        async with factory() as session:
            try:
                next_id = (await session.execute(text(f'SELECT IFNULL(MAX(id), 0) + 1 FROM {self.TABLE}'))).scalar() or 1
                user_id_formatted = f'USER-{next_id}'
                await session.execute(text(f'\n                INSERT INTO {self.TABLE} (\n                    external_id, user_id_formatted, name, email, password_hash, role, phone, company_name, gst_number,\n                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,\n                    is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                    bank_account_number, bank_ifsc_code, bank_account_holder, bank_name,\n                    created_at, updated_at\n                ) VALUES (\n                    :external_id, :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name, :gst_number,\n                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,\n                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,\n                    :is_on_duty, :commission_override_pct, :upi_id, :qr_code_url,\n                    :bank_account_number, :bank_ifsc_code, :bank_account_holder, :bank_name,\n                    :created_at, :updated_at\n                )\n            '), {'external_id': external_id, 'user_id_formatted': user_id_formatted, 'name': data.name or 'Customer', 'email': data.email, 'password_hash': data.password, 'role': data.role if data.role is not None else 'customer', 'phone': data.phone or None, 'company_name': data.company_name, 'gst_number': data.gstin, 'is_active': 1 if (data.is_active if data.is_active is not None else True) else 0, 'approval_status': data.approval_status if data.approval_status is not None else 'approved', 'is_deactivated': 1 if data.is_deactivated else 0, 'credit_limit': data.credit_limit if data.credit_limit is not None else 0, 'credit_used': data.credit_used if data.credit_used is not None else 0, 'payment_terms': str(data.payment_terms if data.payment_terms is not None else '30'), 'assigned_salesperson': data.assigned_salesperson, 'is_email_verified': 1 if (data.is_email_verified if data.is_email_verified is not None else False) else 0, 'referral_code': data.referral_code, 'is_seller_admin': 1 if data.is_seller_admin else 0, 'is_on_duty': 1 if data.is_on_duty else 0, 'commission_override_pct': data.commission_override_pct, 'upi_id': data.upi_id, 'qr_code_url': data.qr_code_url, 'bank_account_number': data.bank_account_number, 'bank_ifsc_code': data.bank_ifsc_code, 'bank_account_holder': data.bank_account_holder, 'bank_name': data.bank_name, 'created_at': now, 'updated_at': now})
                new_id = (await session.execute(text(f'SELECT id FROM {self.TABLE} WHERE external_id = :eid'), {'eid': external_id})).scalar()
                temp_user = User(
                    _id=str(new_id),
                    userId=new_id,
                    userIdFormatted=user_id_formatted,
                    name=data.name,
                    email=data.email,
                    password=data.password,
                    role=data.role,
                    phone=data.phone,
                    companyName=data.company_name,
                    gstin=data.gstin,
                    address=data.address,
                    savedAddresses=data.saved_addresses if data.saved_addresses else [],
                    isActive=data.is_active if data.is_active is not None else True,
                    approvalStatus=data.approval_status if data.approval_status is not None else 'approved',
                    isDeactivated=data.is_deactivated if data.is_deactivated is not None else False,
                    creditLimit=data.credit_limit if data.credit_limit is not None else 0.0,
                    creditUsed=data.credit_used if data.credit_used is not None else 0.0,
                    paymentTerms=data.payment_terms,
                    assignedSalesperson=data.assigned_salesperson,
                    isEmailVerified=data.is_email_verified if data.is_email_verified is not None else False,
                    referralCode=data.referral_code,
                    isSellerAdmin=data.is_seller_admin if data.is_seller_admin is not None else False,
                    serviceAreaZones=data.serviceAreaZones if data.serviceAreaZones else [],
                    isOnDuty=data.is_on_duty if data.is_on_duty is not None else False,
                    commissionOverridePct=data.commission_override_pct,
                    upiId=data.upi_id,
                    qrCodeUrl=data.qr_code_url,
                    bankAccountNumber=data.bank_account_number,
                    bankIfscCode=data.bank_ifsc_code,
                    bankAccountHolder=data.bank_account_holder,
                    bankName=data.bank_name,
                    createdAt=now,
                    updatedAt=now
                )
                await self._replace_children(session, new_id, temp_user)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
        return await self.findById(str(new_id))

    async def add_credit_used_atomic(self, id: str, amount: float) -> bool:
        factory = self._factory()
        if not factory:
            return False
        uid = int(id) if str(id).isdigit() else None
        if uid == 0:
            return False
        from sqlalchemy import text
        async with factory() as session:
            try:
                res = await session.execute(text(f'\n                    UPDATE {self.TABLE} \n                    SET credit_used = COALESCE(credit_used, 0) + :amount,\n                        updated_at = UTC_TIMESTAMP()\n                    WHERE id = :uid \n                    AND (credit_limit IS NULL OR credit_limit = 0 OR COALESCE(credit_used, 0) + :amount <= credit_limit)\n                '), {'uid': uid, 'amount': amount})
                await session.commit()
                return res.rowcount > 0


            except Exception as e:
                await session.rollback()
                raise e
    async def update(self, id: str, update_data: Any) -> Optional[User]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        now = datetime.now(timezone.utc)
        factory = self._factory()
        
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
        async with factory() as session:
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
                    WHERE id = :id
                '''), {
                    'id': int(id) if str(id).isdigit() else None,
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
                    'payment_terms': str(payment_terms) if payment_terms is not None else None,
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
            
                child_keys = ['address', 'savedAddresses', 'serviceAreaZones']
                has_child_updates = False
                for k in child_keys:
                    if k in update_data.model_fields_set:
                        has_child_updates = True
                        
                if has_child_updates:
                    fields_set = update_data.model_fields_set
                    if "address" in fields_set:
                        existing.address = update_data.address
                    if "savedAddresses" in fields_set:
                        existing.saved_addresses = update_data.saved_addresses
                    if "serviceAreaZones" in fields_set:
                        existing.service_area_zones = update_data.service_area_zones
                            
                    await self._replace_children(session, int(id) if str(id).isdigit() else None, existing)
                
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
        return await self.findById(id)
    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            try:
                result = await session.execute(text(f'DELETE FROM {self.TABLE} WHERE id = :id'), {'id': int(id) if str(id).isdigit() else None})
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