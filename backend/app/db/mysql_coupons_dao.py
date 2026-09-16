import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import CouponCreate, CouponUpdate, CouponResponse

from app.config.database import get_async_session_factory

class MySQLCouponsDAO:
    def _factory(self):
        return get_async_session_factory()

    async def create(self, data: CouponCreate) -> CouponResponse:
        async with self._factory()() as session:
            coupon_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            insert_query = text("""
                INSERT INTO sj_coupons (
                    id, code, description, discount_type, discount_value, min_order_value, max_discount,
                    valid_from, valid_until, usage_limit, used_count, is_active, is_public,
                    first_order_only, platform, applies_to, max_usage_per_user, requires_bank,
                    bank_name, terms_and_conditions, created_at, updated_at
                ) VALUES (
                    :id, :code, :description, :discountType, :discountValue, :minOrderValue, :maxDiscount,
                    :validFrom, :validUntil, :usageLimit, :usedCount, :isActive, :isPublic,
                    :firstOrderOnly, :platform, :appliesTo, :maxUsagePerUser, :requiresBank,
                    :bankName, :termsAndConditions, :created_at, :updated_at
                )
            """)

            params = {
                "id": coupon_id,
                "created_at": now,
                "updated_at": now,
            }
            
            try: params["code"] = data.code
            except AttributeError: params["code"] = None
            try: params["description"] = data.description
            except AttributeError: params["description"] = None
            try: params["discountType"] = data.discountType
            except AttributeError: params["discountType"] = None
            try: params["discountValue"] = data.discountValue
            except AttributeError: params["discountValue"] = None
            try: params["minOrderValue"] = data.minOrderValue
            except AttributeError: params["minOrderValue"] = None
            try: params["maxDiscount"] = data.maxDiscount
            except AttributeError: params["maxDiscount"] = None
            try: params["validFrom"] = data.validFrom
            except AttributeError: params["validFrom"] = None
            try: params["validUntil"] = data.validUntil
            except AttributeError: params["validUntil"] = None
            try: params["usageLimit"] = data.usageLimit
            except AttributeError: params["usageLimit"] = None
            try: params["usedCount"] = data.usedCount
            except AttributeError: params["usedCount"] = None
            try: params["isActive"] = data.isActive
            except AttributeError: params["isActive"] = None
            try: params["isPublic"] = data.isPublic
            except AttributeError: params["isPublic"] = None
            try: params["firstOrderOnly"] = data.firstOrderOnly
            except AttributeError: params["firstOrderOnly"] = None
            try: params["platform"] = data.platform
            except AttributeError: params["platform"] = None
            try: params["appliesTo"] = data.appliesTo
            except AttributeError: params["appliesTo"] = None
            try: params["maxUsagePerUser"] = data.maxUsagePerUser
            except AttributeError: params["maxUsagePerUser"] = None
            try: params["requiresBank"] = data.requiresBank
            except AttributeError: params["requiresBank"] = None
            try: params["bankName"] = data.bankName
            except AttributeError: params["bankName"] = None
            try: params["termsAndConditions"] = data.termsAndConditions
            except AttributeError: params["termsAndConditions"] = None

            await session.execute(insert_query, params)

            try:
                quantityTiers = data.quantityTiers
            except AttributeError:
                quantityTiers = None
            if quantityTiers:
                qt_query = text("INSERT INTO sj_coupon_quantity_tiers (coupon_id, min_qty, discount_value) VALUES (:coupon_id, :min_qty, :discount_value)")
                for item in quantityTiers:
                    await session.execute(qt_query, {"coupon_id": coupon_id, "min_qty": item.minQuantity, "discount_value": item.discountValue})

            try:
                applicableRoles = data.applicableRoles
            except AttributeError:
                applicableRoles = None
            if applicableRoles:
                ar_query = text("INSERT INTO sj_coupon_roles (coupon_id, role) VALUES (:coupon_id, :val)")
                for item in applicableRoles:
                    await session.execute(ar_query, {"coupon_id": coupon_id, "val": item})

            try:
                applicableUserIds = data.applicableUserIds
            except AttributeError:
                applicableUserIds = None
            if applicableUserIds:
                au_query = text("INSERT INTO sj_coupon_users (coupon_id, user_id) VALUES (:coupon_id, :val)")
                for item in applicableUserIds:
                    await session.execute(au_query, {"coupon_id": coupon_id, "val": item})

            try:
                applicableCategories = data.applicableCategories
            except AttributeError:
                applicableCategories = None
            if applicableCategories:
                ac_query = text("INSERT INTO sj_coupon_categories (coupon_id, category) VALUES (:coupon_id, :val)")
                for item in applicableCategories:
                    await session.execute(ac_query, {"coupon_id": coupon_id, "val": item})

            try:
                appliesToValueIds = data.appliesToValueIds
            except AttributeError:
                appliesToValueIds = None
            if appliesToValueIds:
                at_query = text("INSERT INTO sj_coupon_applies_to_values (coupon_id, value_id) VALUES (:coupon_id, :val)")
                for item in appliesToValueIds:
                    await session.execute(at_query, {"coupon_id": coupon_id, "val": item})

            try:
                excludedProductIds = data.excludedProductIds
            except AttributeError:
                excludedProductIds = None
            if excludedProductIds:
                ep_query = text("INSERT INTO sj_coupon_excluded_products (coupon_id, product_id) VALUES (:coupon_id, :val)")
                for item in excludedProductIds:
                    await session.execute(ep_query, {"coupon_id": coupon_id, "val": item})

            await session.commit()
            return await self.findById(coupon_id)


    async def update(self, id: str, data: CouponUpdate) -> Optional[CouponResponse]:
        async with self._factory()() as session:
            updates = []
            params = {"id": id, "updated_at": datetime.now(timezone.utc).isoformat()}
            
            try:
                if data.code is not None:
                    updates.append("code = :code")
                    params["code"] = data.code
            except AttributeError: pass
            try:
                if data.description is not None:
                    updates.append("description = :description")
                    params["description"] = data.description
            except AttributeError: pass
            try:
                if data.discountType is not None:
                    updates.append("discount_type = :discountType")
                    params["discountType"] = data.discountType
            except AttributeError: pass
            try:
                if data.discountValue is not None:
                    updates.append("discount_value = :discountValue")
                    params["discountValue"] = data.discountValue
            except AttributeError: pass
            try:
                if data.minOrderValue is not None:
                    updates.append("min_order_value = :minOrderValue")
                    params["minOrderValue"] = data.minOrderValue
            except AttributeError: pass
            try:
                if data.maxDiscount is not None:
                    updates.append("max_discount = :maxDiscount")
                    params["maxDiscount"] = data.maxDiscount
            except AttributeError: pass
            try:
                if data.validFrom is not None:
                    updates.append("valid_from = :validFrom")
                    params["validFrom"] = data.validFrom
            except AttributeError: pass
            try:
                if data.validUntil is not None:
                    updates.append("valid_until = :validUntil")
                    params["validUntil"] = data.validUntil
            except AttributeError: pass
            try:
                if data.usageLimit is not None:
                    updates.append("usage_limit = :usageLimit")
                    params["usageLimit"] = data.usageLimit
            except AttributeError: pass
            try:
                if data.usedCount is not None:
                    updates.append("used_count = :usedCount")
                    params["usedCount"] = data.usedCount
            except AttributeError: pass
            try:
                if data.isActive is not None:
                    updates.append("is_active = :isActive")
                    params["isActive"] = data.isActive
            except AttributeError: pass
            try:
                if data.isPublic is not None:
                    updates.append("is_public = :isPublic")
                    params["isPublic"] = data.isPublic
            except AttributeError: pass
            try:
                if data.firstOrderOnly is not None:
                    updates.append("first_order_only = :firstOrderOnly")
                    params["firstOrderOnly"] = data.firstOrderOnly
            except AttributeError: pass
            try:
                if data.platform is not None:
                    updates.append("platform = :platform")
                    params["platform"] = data.platform
            except AttributeError: pass
            try:
                if data.appliesTo is not None:
                    updates.append("applies_to = :appliesTo")
                    params["appliesTo"] = data.appliesTo
            except AttributeError: pass
            try:
                if data.maxUsagePerUser is not None:
                    updates.append("max_usage_per_user = :maxUsagePerUser")
                    params["maxUsagePerUser"] = data.maxUsagePerUser
            except AttributeError: pass
            try:
                if data.requiresBank is not None:
                    updates.append("requires_bank = :requiresBank")
                    params["requiresBank"] = data.requiresBank
            except AttributeError: pass
            try:
                if data.bankName is not None:
                    updates.append("bank_name = :bankName")
                    params["bankName"] = data.bankName
            except AttributeError: pass
            try:
                if data.termsAndConditions is not None:
                    updates.append("terms_and_conditions = :termsAndConditions")
                    params["termsAndConditions"] = data.termsAndConditions
            except AttributeError: pass

            if updates:
                updates.append("updated_at = :updated_at")
                set_clause = ", ".join(updates)
                update_query = text(f"UPDATE sj_coupons SET {set_clause} WHERE id = :id")
                await session.execute(update_query, params)

            try:
                quantityTiers = data.quantityTiers
                if quantityTiers is not None:
                    await session.execute(text("DELETE FROM sj_coupon_quantity_tiers WHERE coupon_id = :id"), {"id": id})
                    if quantityTiers:
                        qt_query = text("INSERT INTO sj_coupon_quantity_tiers (coupon_id, min_qty, discount_value) VALUES (:coupon_id, :min_qty, :discount_value)")
                        for item in quantityTiers:
                            await session.execute(qt_query, {"coupon_id": id, "min_qty": item.minQuantity, "discount_value": item.discountValue})
            except AttributeError:
                pass

            try:
                applicableRoles = data.applicableRoles
                if applicableRoles is not None:
                    await session.execute(text("DELETE FROM sj_coupon_roles WHERE coupon_id = :id"), {"id": id})
                    if applicableRoles:
                        ar_query = text("INSERT INTO sj_coupon_roles (coupon_id, role) VALUES (:coupon_id, :val)")
                        for item in applicableRoles:
                            await session.execute(ar_query, {"coupon_id": id, "val": item})
            except AttributeError:
                pass

            try:
                applicableUserIds = data.applicableUserIds
                if applicableUserIds is not None:
                    await session.execute(text("DELETE FROM sj_coupon_users WHERE coupon_id = :id"), {"id": id})
                    if applicableUserIds:
                        au_query = text("INSERT INTO sj_coupon_users (coupon_id, user_id) VALUES (:coupon_id, :val)")
                        for item in applicableUserIds:
                            await session.execute(au_query, {"coupon_id": id, "val": item})
            except AttributeError:
                pass

            try:
                applicableCategories = data.applicableCategories
                if applicableCategories is not None:
                    await session.execute(text("DELETE FROM sj_coupon_categories WHERE coupon_id = :id"), {"id": id})
                    if applicableCategories:
                        ac_query = text("INSERT INTO sj_coupon_categories (coupon_id, category) VALUES (:coupon_id, :val)")
                        for item in applicableCategories:
                            await session.execute(ac_query, {"coupon_id": id, "val": item})
            except AttributeError:
                pass

            try:
                appliesToValueIds = data.appliesToValueIds
                if appliesToValueIds is not None:
                    await session.execute(text("DELETE FROM sj_coupon_applies_to_values WHERE coupon_id = :id"), {"id": id})
                    if appliesToValueIds:
                        at_query = text("INSERT INTO sj_coupon_applies_to_values (coupon_id, value_id) VALUES (:coupon_id, :val)")
                        for item in appliesToValueIds:
                            await session.execute(at_query, {"coupon_id": id, "val": item})
            except AttributeError:
                pass

            try:
                excludedProductIds = data.excludedProductIds
                if excludedProductIds is not None:
                    await session.execute(text("DELETE FROM sj_coupon_excluded_products WHERE coupon_id = :id"), {"id": id})
                    if excludedProductIds:
                        ep_query = text("INSERT INTO sj_coupon_excluded_products (coupon_id, product_id) VALUES (:coupon_id, :val)")
                        for item in excludedProductIds:
                            await session.execute(ep_query, {"coupon_id": id, "val": item})
            except AttributeError:
                pass

            await session.commit()
            return await self.findById(id)


    async def findById(self, id: str) -> Optional[CouponResponse]:
        async with self._factory()() as session:
            query = text("SELECT * FROM sj_coupons WHERE id = :id")
            result = await session.execute(query, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            return await self._map_to_response(row)


    async def findOne(self, query=None, **kwargs) -> Optional[CouponResponse]:
        if query:
            kwargs.update(query)
        async with self._factory()() as session:
            if not kwargs:
                return None
            conditions = []
            params = {}
            for k, v in kwargs.items():
                conditions.append(f"{k} = :{k}")
                params[k] = v
            where_clause = " AND ".join(conditions)
            query = text(f"SELECT * FROM sj_coupons WHERE {where_clause} LIMIT 1")
            result = await session.execute(query, params)
            row = result.fetchone()
            if not row:
                return None
            return await self._map_to_response(row)


    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[CouponResponse]:
        query = query or {}
        async with self._factory()() as session:
            sql = "SELECT * FROM sj_coupons"
            params = {}
            if query:
                conditions = []
                for k, v in query.items():
                    if k == "isActive":
                        conditions.append("is_active = :isActive")
                        params["isActive"] = int(v) if isinstance(v, bool) else v
                    elif k == "method":
                        conditions.append("method = :method")
                        params["method"] = v
                    elif k == "typeOfDiscount":
                        conditions.append("type_of_discount = :typeOfDiscount")
                        params["typeOfDiscount"] = v
                    elif k == "id":
                        conditions.append("id = :id")
                        params["id"] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            responses = []
            for row in rows:
                responses.append(await self._map_to_response(row))
            return responses


    async def _map_to_response(self, row) -> CouponResponse:
        async with self._factory()() as session:
            coupon_id = row.id

            response_data = {
                "id": coupon_id,
                "code": row.code,
                "description": row.description,
                "discountType": row.discount_type,
                "discountValue": row.discount_value,
                "minOrderValue": row.min_order_value,
                "maxDiscount": row.max_discount,
                "validFrom": row.valid_from,
                "validUntil": row.valid_until,
                "usageLimit": row.usage_limit,
                "usedCount": row.used_count,
                "isActive": bool(row.is_active) if row.is_active is not None else None,
                "isPublic": bool(row.is_public) if row.is_public is not None else None,
                "firstOrderOnly": bool(row.first_order_only) if row.first_order_only is not None else None,
                "platform": row.platform,
                "appliesTo": row.applies_to,
                "maxUsagePerUser": row.max_usage_per_user,
                "requiresBank": bool(row.requires_bank) if row.requires_bank is not None else None,
                "bankName": row.bank_name,
                "termsAndConditions": row.terms_and_conditions,
                "createdAt": str(row.created_at),
                "updatedAt": str(row.updated_at)
            }

            qt_res = await session.execute(text("SELECT * FROM sj_coupon_quantity_tiers WHERE coupon_id = :id"), {"id": coupon_id})
            qt_rows = qt_res.fetchall()
            response_data["quantityTiers"] = [{"minQuantity": r.min_qty, "discountValue": r.discount_value} for r in qt_rows]

            ar_res = await session.execute(text("SELECT * FROM sj_coupon_roles WHERE coupon_id = :id"), {"id": coupon_id})
            ar_rows = ar_res.fetchall()
            response_data["applicableRoles"] = [r.role for r in ar_rows]

            au_res = await session.execute(text("SELECT * FROM sj_coupon_users WHERE coupon_id = :id"), {"id": coupon_id})
            au_rows = au_res.fetchall()
            response_data["applicableUserIds"] = [r.user_id for r in au_rows]

            ac_res = await session.execute(text("SELECT * FROM sj_coupon_categories WHERE coupon_id = :id"), {"id": coupon_id})
            ac_rows = ac_res.fetchall()
            response_data["applicableCategories"] = [r.category for r in ac_rows]

            at_res = await session.execute(text("SELECT * FROM sj_coupon_applies_to_values WHERE coupon_id = :id"), {"id": coupon_id})
            at_rows = at_res.fetchall()
            response_data["appliesToValueIds"] = [r.value_id for r in at_rows]

            ep_res = await session.execute(text("SELECT * FROM sj_coupon_excluded_products WHERE coupon_id = :id"), {"id": coupon_id})
            ep_rows = ep_res.fetchall()
            response_data["excludedProductIds"] = [r.product_id for r in ep_rows]

            return CouponResponse(**response_data)

