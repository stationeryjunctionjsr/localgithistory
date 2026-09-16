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

    def clean_terms(t):
        if not t:
            return None
        t_str = str(t).replace('net_', '')
        return int(t_str) if t_str.isdigit() else None
    all_addresses = children['addresses'] if 'addresses' in children else []
    address = next((a for a in all_addresses if (a['isPrimary'] if 'isPrimary' in a else None)), {})
    saved_addresses = [a for a in all_addresses if not (a['isPrimary'] if 'isPrimary' in a else None)]
    seller_permissions = {'serviceablePincodes': children['serviceablePincodes'] if 'serviceablePincodes' in children else [], 'urgentPincodes': children['urgentPincodes'] if 'urgentPincodes' in children else [], 'slotPincodes': children['slotPincodes'] if 'slotPincodes' in children else [], 'serviceableZoneIds': children['serviceableZoneIds'] if 'serviceableZoneIds' in children else []}
    is_seller_admin_val = r.is_seller_admin
    is_on_duty_val = r.is_on_duty
    commission_override_val = r.commission_override_pct
    return User(**{'_id': str(r.id), 'userId': r.id, 'userIdFormatted': r.user_id_formatted or (f'USER-{r.id}' if r.id else None), 'name': r.name, 'email': r.email, 'password': r.password_hash, 'role': r.role, 'phone': r.phone or '', 'companyName': r.company_name, 'address': address, 'savedAddresses': saved_addresses, 'isActive': bool(r.is_active) if r.is_active is not None else True, 'approvalStatus': r.approval_status, 'isDeactivated': bool(r.is_deactivated) if r.is_deactivated is not None else False, 'creditLimit': float(r.credit_limit) if r.credit_limit is not None else 0, 'creditUsed': float(r.credit_used) if r.credit_used is not None else 0, 'paymentTerms': clean_terms(r.payment_terms), 'assignedSalesperson': r.assigned_salesperson, 'isEmailVerified': bool(r.is_email_verified) if r.is_email_verified is not None else False, 'referralCode': r.referral_code, 'isSellerAdmin': bool(is_seller_admin_val) if is_seller_admin_val is not None else False, 'sellerPermissions': seller_permissions, 'serviceAreaZones': children['zones'] if 'zones' in children else [], 'isOnDuty': bool(is_on_duty_val) if is_on_duty_val is not None else False, 'commissionOverridePct': float(commission_override_val) if commission_override_val is not None else None, 'createdAt': r.created_at, 'updatedAt': r.updated_at})

class MySQLUserDAO:

    @property
    def TABLE(self):
        suffix = settings.table_suffix if settings.table_suffix is not None else ''
        return f'sj_users{suffix}'

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
        if 'referralCode' in query:
            where_clauses.append('UPPER(referral_code) = :referralCode')
            params['referralCode'] = query['referralCode'].upper()
        if 'isSellerAdmin' in query:
            where_clauses.append('is_seller_admin = :isSellerAdmin')
            params['isSellerAdmin'] = 1 if query['isSellerAdmin'] else 0
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
        children_map = {uid: {'addresses': [], 'serviceablePincodes': [], 'urgentPincodes': [], 'slotPincodes': [], 'zones': [], 'serviceableZoneIds': []} for uid in uids}
        if not uids:
            return children_map
        chunks = [uids[i:i + 999] for i in range(0, len(uids), 999)]
        for chunk in chunks:
            chunk_params = {f'uid_{i}': uid for i, uid in enumerate(chunk)}
            placeholders = ', '.join([f':{k}' for k in chunk_params.keys()])
            res = await session.execute(text(f'SELECT user_id, is_primary, street, city, state, pincode, phone FROM sj_user_addresses WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                children_map[r.user_id]['addresses'].append({'isPrimary': bool(r.is_primary), 'street': r.street, 'city': r.city, 'state': r.state, 'pincode': r.pincode, 'phone': r.phone})
            res = await session.execute(text(f'SELECT user_id, pincode, pincode_type FROM sj_seller_pincodes WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                if r.pincode_type == 'serviceable':
                    children_map[r.user_id]['serviceablePincodes'].append(r.pincode)
                elif r.pincode_type == 'urgent':
                    children_map[r.user_id]['urgentPincodes'].append(r.pincode)
                elif r.pincode_type == 'slot':
                    children_map[r.user_id]['slotPincodes'].append(r.pincode)
            res = await session.execute(text(f'SELECT user_id, zone_name, zone_id FROM sj_seller_zones WHERE user_id IN ({placeholders})'), chunk_params)
            for r in res.fetchall():
                children_map[r.user_id]['zones'].append(r.zone_name)
                if r.zone_id:
                    children_map[r.user_id]['serviceableZoneIds'].append(r.zone_id)
        return children_map

    async def _replace_children(self, session, uid: int, data: User):
        await session.execute(text('DELETE FROM sj_user_addresses WHERE user_id = :uid'), {'uid': uid})
        await session.execute(text('DELETE FROM sj_seller_pincodes WHERE user_id = :uid'), {'uid': uid})
        await session.execute(text('DELETE FROM sj_seller_zones WHERE user_id = :uid'), {'uid': uid})
        address = data.address
        saved_addresses = data.savedAddresses if data.savedAddresses is not None else []
        if address:
            await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone) VALUES (:uid, 1, :st, :c, :s, :p, :ph)'), {'uid': uid, 'st': address.street, 'c': address.city, 's': address.state, 'p': address.pincode, 'ph': address.phone})
        for a in saved_addresses:
            if a != address:
                await session.execute(text('INSERT INTO sj_user_addresses (user_id, is_primary, street, city, state, pincode, phone) VALUES (:uid, 0, :st, :c, :s, :p, :ph)'), {'uid': uid, 'st': a.street, 'c': a.city, 's': a.state, 'p': a.pincode, 'ph': a.phone})
        seller_perms = data.sellerPermissions
        if seller_perms:
            for p in seller_perms.serviceablePincodes if seller_perms.serviceablePincodes is not None else []:
                await session.execute(text("INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'serviceable')"), {'uid': uid, 'p': p})
            for p in seller_perms.urgentPincodes if seller_perms.urgentPincodes is not None else []:
                await session.execute(text("INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'urgent')"), {'uid': uid, 'p': p})
            for p in seller_perms.slotPincodes if seller_perms.slotPincodes is not None else []:
                await session.execute(text("INSERT INTO sj_seller_pincodes (user_id, pincode, pincode_type) VALUES (:uid, :p, 'slot')"), {'uid': uid, 'p': p})
        for zone_ext_id in data.serviceAreaZones if data.serviceAreaZones is not None else []:
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
            query_str = f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC\n            '
            if limit is not None:
                query_str += f' LIMIT {int(limit)}'
            if skip is not None:
                query_str += f' OFFSET {int(skip)}'
            rows = (await session.execute(text(query_str), params)).fetchall()
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
        from app.models.user import User
        docs = [UserResponse.model_validate(_map_to_schema(r, children_map[int(r.id)] if int(r.id) in children_map else {})) for r in rows]
        if query:
            filtered = []
            for doc in docs:
                match = True
                for k, v in query.items():
                    if k in ('allowed_ids',):
                        continue
                    if k in ('_id', 'id'):
                        if doc.id != str(v) and doc.id != v:
                            match = False
                            break
                    elif (doc[k] if k in doc else None) != v:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            return filtered
        return docs

    async def findOne(self, query: Dict) -> Optional[User]:
        if set(query.keys()) in ({'_id'}, {'id'}):
            return await self.findById((query['_id'] if '_id' in query else None) or (query['id'] if 'id' in query else None))
        if set(query.keys()) == {'email'} and (query['email'] if 'email' in query else None):
            return await self.findByEmail(query['email'])
        if set(query.keys()) == {'phone'} and (query['phone'] if 'phone' in query else None):
            return await self.findByPhone(query['phone'])
        if set(query.keys()) == {'referralCode'} and (query['referralCode'] if 'referralCode' in query else None):
            return await self.findByReferralCode(query['referralCode'])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[User]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE id = :id\n            '), {'id': int(id) if str(id).isdigit() else None})).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByEmail(self, email: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not email:
            return None
        async with factory() as session:
            row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE LOWER(email) = :email LIMIT 1\n            '), {'email': email.lower()})).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByPhone(self, phone: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not phone:
            return None
        normalized = ''.join(filter(str.isdigit, phone))
        if not normalized:
            return None
        async with factory() as session:
            row = (await session.execute(text(f"\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE phone = :phone OR REGEXP_REPLACE(phone, '[^0-9]', '') = :normalized LIMIT 1\n            "), {'phone': phone, 'normalized': normalized})).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _map_to_schema(row, children_map[int(row.id)])

    async def findByReferralCode(self, referral_code: str) -> Optional[User]:
        factory = self._factory()
        if not factory or not referral_code:
            return None
        async with factory() as session:
            row = (await session.execute(text(f'\n                SELECT id, external_id, user_id_formatted, name, email, password_hash,\n                       role, phone, company_name, is_active,\n                       approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                       assigned_salesperson, is_email_verified, referral_code,\n                       is_seller_admin, is_on_duty, commission_override_pct, upi_id, qr_code_url,\n                       created_at, updated_at\n                FROM {self.TABLE} WHERE UPPER(referral_code) = :referral_code LIMIT 1\n            '), {'referral_code': referral_code.upper()})).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
        return _map_to_schema(row, children_map[int(row.id)])

    async def create(self, data: UserInternalCreate) -> User:
        external_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        factory = self._factory()
        if not factory:
            raise RuntimeError('MySQL not configured')
        async with factory() as session:
            next_id = (await session.execute(text(f'SELECT IFNULL(MAX(id), 0) + 1 FROM {self.TABLE}'))).scalar() or 1
            user_id_formatted = f'USER-{next_id}'
            await session.execute(text(f'\n                INSERT INTO {self.TABLE} (\n                    external_id, user_id_formatted, name, email, password_hash, role, phone, company_name,\n                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,\n                    is_on_duty, commission_override_pct, upi_id, qr_code_url, created_at, updated_at\n                ) VALUES (\n                    :external_id, :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name,\n                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,\n                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,\n                    :is_on_duty, :commission_override_pct, :upi_id, :qr_code_url, :created_at, :updated_at\n                )\n            '), {'external_id': external_id, 'user_id_formatted': user_id_formatted, 'name': data.name or 'Customer', 'email': data.email, 'password_hash': data.password, 'role': data.role if data.role is not None else 'customer', 'phone': data.phone or None, 'company_name': data.companyName, 'is_active': 1 if (data.isActive if data.isActive is not None else True) else 0, 'approval_status': data.approvalStatus if data.approvalStatus is not None else 'approved', 'is_deactivated': 1 if data.isDeactivated else 0, 'credit_limit': data.creditLimit if data.creditLimit is not None else 0, 'credit_used': data.creditUsed if data.creditUsed is not None else 0, 'payment_terms': str(data.paymentTerms if data.paymentTerms is not None else '30'), 'assigned_salesperson': data.assignedSalesperson, 'is_email_verified': 1 if (data.isEmailVerified if data.isEmailVerified is not None else False) else 0, 'referral_code': data.referralCode, 'is_seller_admin': 1 if data.isSellerAdmin else 0, 'is_on_duty': 1 if data.isOnDuty else 0, 'commission_override_pct': data.commissionOverridePct, 'upi_id': getattr(data, 'upiId', None), 'qr_code_url': getattr(data, 'qrCodeUrl', None), 'created_at': now, 'updated_at': now})
            new_id = (await session.execute(text(f'SELECT id FROM {self.TABLE} WHERE external_id = :eid'), {'eid': external_id})).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
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
            res = await session.execute(text(f'\n                    UPDATE {self.TABLE} \n                    SET credit_used = COALESCE(credit_used, 0) + :amount,\n                        updated_at = UTC_TIMESTAMP()\n                    WHERE id = :uid \n                    AND (credit_limit IS NULL OR credit_limit = 0 OR COALESCE(credit_used, 0) + :amount <= credit_limit)\n                '), {'uid': uid, 'amount': amount})
            await session.commit()
            return res.rowcount > 0


    async def update(self, id: str, update_data: Any) -> Optional[User]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        now = datetime.now(timezone.utc)
        factory = self._factory()
        
        # Manually extract fields from the Pydantic update_data model, falling back to existing dict
        name = (update_data.name if update_data.name is not None else existing.name)
        email = (update_data.email if update_data.email is not None else existing.email)
        password_hash = (update_data.password if update_data.password is not None else existing.password)
        role = (update_data.role if update_data.role is not None else existing.role)
        phone = (update_data.phone if update_data.phone is not None else existing.phone)
        company_name = (update_data.companyName if update_data.companyName is not None else existing.companyName)
        is_active = (update_data.isActive if update_data.isActive is not None else existing.isActive)
        approval_status = (update_data.approvalStatus if update_data.approvalStatus is not None else existing.approvalStatus)
        is_deactivated = (update_data.isDeactivated if update_data.isDeactivated is not None else existing.isDeactivated)
        credit_limit = (update_data.creditLimit if update_data.creditLimit is not None else existing.creditLimit)
        credit_used = (update_data.creditUsed if update_data.creditUsed is not None else existing.creditUsed)
        payment_terms = (update_data.paymentTerms if update_data.paymentTerms is not None else existing.paymentTerms)
        assigned_salesperson = (update_data.assignedSalesperson if update_data.assignedSalesperson is not None else existing.assignedSalesperson)
        is_email_verified = (update_data.isEmailVerified if update_data.isEmailVerified is not None else existing.isEmailVerified)
        referral_code = (update_data.referralCode if update_data.referralCode is not None else existing.referralCode)
        is_seller_admin = (update_data.isSellerAdmin if update_data.isSellerAdmin is not None else existing.isSellerAdmin)
        is_on_duty = (update_data.isOnDuty if update_data.isOnDuty is not None else existing.isOnDuty)
        commission_override_pct = (update_data.commissionOverridePct if update_data.commissionOverridePct is not None else existing.commissionOverridePct)
        upi_id = (update_data.upiId if update_data.upiId is not None else existing.upiId)
        qr_code_url = (update_data.qrCodeUrl if update_data.qrCodeUrl is not None else existing.qrCodeUrl)

        async with factory() as session:
            await session.execute(text('''
                UPDATE sj_users SET
                    name = :name, email = :email, password_hash = :password_hash, role = :role, phone = :phone,
                    company_name = :company_name, is_active = :is_active, approval_status = :approval_status,
                    is_deactivated = :is_deactivated, credit_limit = :credit_limit, credit_used = :credit_used,
                    payment_terms = :payment_terms, assigned_salesperson = :assigned_salesperson,
                    is_email_verified = :is_email_verified, referral_code = :referral_code, is_seller_admin = :is_seller_admin,
                    is_on_duty = :is_on_duty, commission_override_pct = :commission_override_pct, upi_id = :upi_id, qr_code_url = :qr_code_url, updated_at = :updated_at
                WHERE id = :id
            '''), {
                'id': int(id) if str(id).isdigit() else None, 
                'name': name, 
                'email': email, 
                'password_hash': password_hash, 
                'role': role, 
                'phone': phone or None, 
                'company_name': company_name, 
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
                'updated_at': now
            })
            await self._replace_children(session, int(id) if str(id).isdigit() else None, update_data)
            await session.commit()
        return await self.findById(id)
    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f'DELETE FROM {self.TABLE} WHERE id = :id'), {'id': int(id) if str(id).isdigit() else None})
            await session.commit()
            return result.rowcount > 0
    find_all = findAll
    find_by_id = findById
    find_one = findOne
    find_by_email = findByEmail
    find_by_phone = findByPhone
    find_by_referral_code = findByReferralCode