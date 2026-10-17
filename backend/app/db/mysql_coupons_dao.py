from typing import Optional, List
from datetime import datetime, timezone
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import (
    CouponInternal,
    CouponInternalCreate,
    CouponInternalUpdate,
    CouponQuantityTierInternal,
    CouponUserUsageInternal,
)

def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class MySQLCouponsDAO:
    def __init__(self):
        self.table_name = "sj_coupons"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    async def findById(self, id: int) -> Optional[CouponInternal]:
        session_factory = get_async_session_factory()
        if not session_factory or not id:
            return None
        async with session_factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            (
                rows_quantity_tiers,
                rows_applicable_roles,
                rows_applicable_user_ids,
                rows_applicable_categories,
                rows_applies_to_value_ids,
                rows_excluded_product_ids,
            ) = await self._fetch_children(session, [row.id])
            return self._map_to_schema(
                row,
                rows_quantity_tiers,
                rows_applicable_roles,
                rows_applicable_user_ids,
                rows_applicable_categories,
                rows_applies_to_value_ids,
                rows_excluded_product_ids,
            )

    async def findByCode(self, code: str) -> Optional[CouponInternal]:
        session_factory = get_async_session_factory()
        if not session_factory or not code:
            return None
        async with session_factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE UPPER(code) = :code LIMIT 1")
            result = await session.execute(q, {"code": code.upper()})
            row = result.fetchone()
            if not row:
                return None
            (
                rows_quantity_tiers,
                rows_applicable_roles,
                rows_applicable_user_ids,
                rows_applicable_categories,
                rows_applies_to_value_ids,
                rows_excluded_product_ids,
            ) = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(
                row,
                rows_quantity_tiers,
                rows_applicable_roles,
                rows_applicable_user_ids,
                rows_applicable_categories,
                rows_applies_to_value_ids,
                rows_excluded_product_ids,
            )

    async def findOne(
        self,
        code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[CouponInternal]:
        if code:
            return await self.findByCode(code)
        results = await self.findAll(is_active=is_active)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        method: Optional[str] = None,
        code: Optional[str] = None,
        type_of_discount: Optional[str] = None,
    ) -> List[CouponInternal]:
        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if method is not None:
            clauses.append("method = :method")
            params["method"] = method
        if code is not None:
            clauses.append("UPPER(code) = :code")
            params["code"] = code.upper()
        if type_of_discount is not None:
            clauses.append("type_of_discount = :type_of_discount")
            params["type_of_discount"] = type_of_discount

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        session_factory = get_async_session_factory()
        if not session_factory:
            return []
        async with session_factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            (
                rows_quantity_tiers,
                rows_applicable_roles,
                rows_applicable_user_ids,
                rows_applicable_categories,
                rows_applies_to_value_ids,
                rows_excluded_product_ids,
            ) = await self._fetch_children(session, [int(r.id) for r in rows])
            return [
                self._map_to_schema(
                    r,
                    rows_quantity_tiers,
                    rows_applicable_roles,
                    rows_applicable_user_ids,
                    rows_applicable_categories,
                    rows_applies_to_value_ids,
                    rows_excluded_product_ids,
                )
                for r in rows
            ]

    async def create(self, data: CouponInternalCreate) -> Optional[CouponInternal]:
        session_factory = get_async_session_factory()
        if not session_factory:
            return None
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}

        if data.code is not None:
            cols.append("code")
            vals.append(":s_code")
            params["s_code"] = data.code

        if data.discount_type is not None:
            cols.append("discount_type")
            vals.append(":s_discountType")
            params["s_discountType"] = data.discount_type

        if data.discount_value is not None:
            cols.append("discount_value")
            vals.append(":s_discountValue")
            params["s_discountValue"] = data.discount_value

        if data.min_purchase_amount is not None:
            cols.append("min_order_value")
            vals.append(":s_minOrderValue")
            params["s_minOrderValue"] = data.min_purchase_amount

        if data.usage_limit is not None:
            cols.append("max_uses")
            vals.append(":s_maxUses")
            params["s_maxUses"] = data.usage_limit

        if data.used_count is not None:
            cols.append("used_count")
            vals.append(":s_usedCount")
            params["s_usedCount"] = data.used_count

        if data.valid_from is not None:
            cols.append("start_date")
            vals.append(":s_validFrom")
            params["s_validFrom"] = data.valid_from

        if data.valid_until is not None:
            cols.append("end_date")
            vals.append(":s_validUntil")
            params["s_validUntil"] = data.valid_until

        if data.is_active is not None:
            cols.append("is_active")
            vals.append(":s_isActive")
            params["s_isActive"] = data.is_active

        if data.type_of_discount is not None:
            cols.append("type_of_discount")
            vals.append(":s_typeOfDiscount")
            params["s_typeOfDiscount"] = data.type_of_discount

        if data.method is not None:
            cols.append("method")
            vals.append(":s_method")
            params["s_method"] = data.method

        if data.min_requirement_type is not None:
            cols.append("min_requirement_type")
            vals.append(":s_minRequirementType")
            params["s_minRequirementType"] = data.min_requirement_type

        if data.min_quantity_of_eligible_items is not None:
            cols.append("min_quantity_of_eligible_items")
            vals.append(":s_minQuantityOfEligibleItems")
            params["s_minQuantityOfEligibleItems"] = data.min_quantity_of_eligible_items

        if data.max_discount_amount is not None:
            cols.append("max_discount_amount")
            vals.append(":s_maxDiscountAmount")
            params["s_maxDiscountAmount"] = data.max_discount_amount

        if data.applies_to_type is not None:
            cols.append("applies_to_type")
            vals.append(":s_appliesToType")
            params["s_appliesToType"] = data.applies_to_type

        if data.display_id is not None:
            cols.append("display_id")
            vals.append(":s_displayId")
            params["s_displayId"] = data.display_id

        if data.buy_x_get_y_customer_gets_quantity is not None:
            cols.append("bxgy_customer_gets_quantity")
            vals.append(":s_bxgy_customer_gets_quantity")
            params["s_bxgy_customer_gets_quantity"] = data.buy_x_get_y_customer_gets_quantity

        if data.buy_x_get_y_customer_gets_applies_to_type is not None:
            cols.append("bxgy_customer_gets_applies_to_type")
            vals.append(":s_bxgy_customer_gets_applies_to_type")
            params["s_bxgy_customer_gets_applies_to_type"] = data.buy_x_get_y_customer_gets_applies_to_type

        if data.buy_x_get_y_customer_gets_applies_to_value_ids is not None:
            cols.append("bxgy_applies_to_ids")
            vals.append(":s_bxgy_applies_to_ids")
            params["s_bxgy_applies_to_ids"] = json.dumps(data.buy_x_get_y_customer_gets_applies_to_value_ids)

        if data.buy_x_get_y_customer_gets_discount_type is not None:
            cols.append("bxgy_discount_type")
            vals.append(":s_bxgy_discount_type")
            params["s_bxgy_discount_type"] = data.buy_x_get_y_customer_gets_discount_type

        if data.buy_x_get_y_customer_gets_discount_value is not None:
            cols.append("bxgy_discount_value")
            vals.append(":s_bxgy_discount_value")
            params["s_bxgy_discount_value"] = data.buy_x_get_y_customer_gets_discount_value

        if data.applicable_item_type is not None:
            cols.append("applicable_item_type")
            vals.append(":s_applicable_item_type")
            params["s_applicable_item_type"] = data.applicable_item_type

        if data.coupon_mode is not None:
            cols.append("coupon_mode")
            vals.append(":s_coupon_mode")
            params["s_coupon_mode"] = data.coupon_mode

        if data.max_usage_per_user is not None:
            cols.append("max_usage_per_user")
            vals.append(":s_max_usage_per_user")
            params["s_max_usage_per_user"] = data.max_usage_per_user

        if data.user_behavior is not None:
            cols.append("user_behavior")
            vals.append(":s_user_behavior")
            params["s_user_behavior"] = data.user_behavior

        if data.applicable_payment_methods is not None:
            cols.append("applicable_payment_methods")
            vals.append(":s_applicable_payment_methods")
            params["s_applicable_payment_methods"] = json.dumps(data.applicable_payment_methods)

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        
        async with session_factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            if data.user_usages:
                await self._replace_user_usages(session, new_id, data.user_usages)
            if data.quantity_tiers:
                await self._replace_quantity_tiers(session, new_id, data.quantity_tiers)
            if data.applicable_roles:
                await self._replace_roles(session, new_id, data.applicable_roles)
            if data.applicable_user_ids:
                await self._replace_users(session, new_id, data.applicable_user_ids)
            if data.applicable_categories:
                await self._replace_categories(session, new_id, data.applicable_categories)
            if data.applies_to_value_ids:
                await self._replace_applies_to_values(session, new_id, data.applies_to_value_ids)
            if data.excluded_product_ids:
                await self._replace_excluded_products(session, new_id, data.excluded_product_ids)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: CouponInternalUpdate) -> Optional[CouponInternal]:
        session_factory = get_async_session_factory()
        if not session_factory or not id:
            return None
        fields = update_data.model_fields_set
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if "code" in fields:
            updates.append("code = :s_code")
            params["s_code"] = update_data.code

        if "discount_type" in fields:
            updates.append("discount_type = :s_discountType")
            params["s_discountType"] = update_data.discount_type

        if "discount_value" in fields:
            updates.append("discount_value = :s_discountValue")
            params["s_discountValue"] = update_data.discount_value

        if "min_purchase_amount" in fields:
            updates.append("min_order_value = :s_minOrderValue")
            params["s_minOrderValue"] = update_data.min_purchase_amount

        if "usage_limit" in fields:
            updates.append("max_uses = :s_maxUses")
            params["s_maxUses"] = update_data.usage_limit

        if "used_count" in fields:
            updates.append("used_count = :s_usedCount")
            params["s_usedCount"] = update_data.used_count

        if "valid_from" in fields:
            updates.append("start_date = :s_validFrom")
            params["s_validFrom"] = update_data.valid_from

        if "valid_until" in fields:
            updates.append("end_date = :s_validUntil")
            params["s_validUntil"] = update_data.valid_until

        if "is_active" in fields:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = update_data.is_active

        if "type_of_discount" in fields:
            updates.append("type_of_discount = :s_typeOfDiscount")
            params["s_typeOfDiscount"] = update_data.type_of_discount

        if "method" in fields:
            updates.append("method = :s_method")
            params["s_method"] = update_data.method

        if "min_requirement_type" in fields:
            updates.append("min_requirement_type = :s_minRequirementType")
            params["s_minRequirementType"] = update_data.min_requirement_type

        if "min_quantity_of_eligible_items" in fields:
            updates.append("min_quantity_of_eligible_items = :s_minQuantityOfEligibleItems")
            params["s_minQuantityOfEligibleItems"] = update_data.min_quantity_of_eligible_items

        if "max_discount_amount" in fields:
            updates.append("max_discount_amount = :s_maxDiscountAmount")
            params["s_maxDiscountAmount"] = update_data.max_discount_amount

        if "applies_to_type" in fields:
            updates.append("applies_to_type = :s_appliesToType")
            params["s_appliesToType"] = update_data.applies_to_type

        if "display_id" in fields:
            updates.append("display_id = :s_displayId")
            params["s_displayId"] = update_data.display_id

        if "buy_x_get_y_customer_gets_quantity" in fields:
            updates.append("bxgy_customer_gets_quantity = :s_bxgy_customer_gets_quantity")
            params["s_bxgy_customer_gets_quantity"] = update_data.buy_x_get_y_customer_gets_quantity

        if "buy_x_get_y_customer_gets_applies_to_type" in fields:
            updates.append("bxgy_customer_gets_applies_to_type = :s_bxgy_customer_gets_applies_to_type")
            params["s_bxgy_customer_gets_applies_to_type"] = update_data.buy_x_get_y_customer_gets_applies_to_type

        if "buy_x_get_y_customer_gets_applies_to_value_ids" in fields:
            updates.append("bxgy_applies_to_ids = :s_bxgy_applies_to_ids")
            params["s_bxgy_applies_to_ids"] = json.dumps(update_data.buy_x_get_y_customer_gets_applies_to_value_ids) if update_data.buy_x_get_y_customer_gets_applies_to_value_ids is not None else None

        if "buy_x_get_y_customer_gets_discount_type" in fields:
            updates.append("bxgy_discount_type = :s_bxgy_discount_type")
            params["s_bxgy_discount_type"] = update_data.buy_x_get_y_customer_gets_discount_type

        if "buy_x_get_y_customer_gets_discount_value" in fields:
            updates.append("bxgy_discount_value = :s_bxgy_discount_value")
            params["s_bxgy_discount_value"] = update_data.buy_x_get_y_customer_gets_discount_value

        if "applicable_item_type" in fields:
            updates.append("applicable_item_type = :s_applicable_item_type")
            params["s_applicable_item_type"] = update_data.applicable_item_type

        if "coupon_mode" in fields:
            updates.append("coupon_mode = :s_coupon_mode")
            params["s_coupon_mode"] = update_data.coupon_mode

        if "max_usage_per_user" in fields:
            updates.append("max_usage_per_user = :s_max_usage_per_user")
            params["s_max_usage_per_user"] = update_data.max_usage_per_user

        if "user_behavior" in fields:
            updates.append("user_behavior = :s_user_behavior")
            params["s_user_behavior"] = update_data.user_behavior

        if "applicable_payment_methods" in fields:
            updates.append("applicable_payment_methods = :s_applicable_payment_methods")
            params["s_applicable_payment_methods"] = json.dumps(update_data.applicable_payment_methods) if update_data.applicable_payment_methods is not None else None

        async with session_factory() as session:
            if len(updates) > 1:
                upd_sql = ", ".join(updates)
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            if "user_usages" in fields:
                await self._replace_user_usages(session, id, update_data.user_usages or [])
            if "quantity_tiers" in fields:
                await self._replace_quantity_tiers(session, id, update_data.quantity_tiers or [])
            if "applicable_roles" in fields:
                await self._replace_roles(session, id, update_data.applicable_roles or [])
            if "applicable_user_ids" in fields:
                await self._replace_users(session, id, update_data.applicable_user_ids or [])
            if "applicable_categories" in fields:
                await self._replace_categories(session, id, update_data.applicable_categories or [])
            if "applies_to_value_ids" in fields:
                await self._replace_applies_to_values(session, id, update_data.applies_to_value_ids or [])
            if "excluded_product_ids" in fields:
                await self._replace_excluded_products(session, id, update_data.excluded_product_ids or [])
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        session_factory = get_async_session_factory()
        if not session_factory or not id:
            return False
        pk = id
        async with session_factory() as session:
            await session.execute(text("DELETE FROM sj_coupon_quantity_tiers WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_roles WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_users WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_categories WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_applies_to_values WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_excluded_products WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_coupon_user_usages WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def getNextDisplayNumber(self, prefix: str) -> int:
        session_factory = get_async_session_factory()
        if not session_factory:
            return 1
        async with session_factory() as session:
            res = await session.execute(
                text(
                    f"SELECT IFNULL(MAX(CAST(REGEXP_SUBSTR(code, '[0-9]+$') AS UNSIGNED)), 0) AS max_num"
                    f" FROM {self.TABLE} WHERE code LIKE :pat"
                ),
                {"pat": f"{prefix}%"},
            )
            row = res.fetchone()
            max_num = int(row.max_num) if row and row.max_num is not None else 0
            return max_num + 1

    def _map_to_schema(
        self,
        r,
        rows_quantityTiers,
        rows_applicableRoles,
        rows_applicableUserIds,
        rows_applicableCategories,
        rows_appliesToValueIds,
        rows_excludedProductIds,
    ) -> 'CouponInternal':
        row_id = int(r.id)
        return CouponInternal(
            id=str(r.id),
            code=r.code,
            discount_type=r.discount_type,
            discount_value=float(r.discount_value) if r.discount_value is not None else None,
            min_order_value=float(r.min_order_value) if r.min_order_value is not None else None,
            max_uses=int(r.max_uses) if r.max_uses is not None else None,
            used_count=int(r.used_count) if r.used_count is not None else 0,
            start_date=r.start_date,
            end_date=r.end_date,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            type_of_discount=r.type_of_discount,
            method=r.method,
            min_requirement_type=r.min_requirement_type,
            min_quantity_of_eligible_items=int(r.min_quantity_of_eligible_items) if r.min_quantity_of_eligible_items is not None else None,
            max_discount_amount=float(r.max_discount_amount) if r.max_discount_amount is not None else None,
            applies_to_type=r.applies_to_type,
            display_id=r.display_id,
            buy_x_get_y_customer_gets_applies_to_type=r.bxgy_customer_gets_applies_to_type,
            buy_x_get_y_customer_gets_quantity=r.bxgy_customer_gets_quantity,
            bxgy_applies_to_ids=None,
            bxgy_discount_type=r.bxgy_discount_type,
            bxgy_discount_value=float(r.bxgy_discount_value) if r.bxgy_discount_value is not None else None,
            applicable_item_type=r.applicable_item_type,
            coupon_mode=r.coupon_mode,
            max_usage_per_user=r.max_usage_per_user,
            user_usages=None,
            user_behavior=r.user_behavior,
            quantity_tiers=[
                CouponQuantityTierInternal(
                    min_quantity=rqt.min_qty,
                    discount_value=float(rqt.discount_value) if rqt.discount_value is not None else None,
                )
                for rqt in rows_quantityTiers
                if int(rqt.parent_id) == row_id
            ],
            applicable_roles=[rar.role for rar in rows_applicableRoles if int(rar.parent_id) == row_id],
            applicable_user_ids=[rau.user_id for rau in rows_applicableUserIds if int(rau.parent_id) == row_id],
            applicable_categories=[rac.category for rac in rows_applicableCategories if int(rac.parent_id) == row_id],
            applies_to_value_ids=[rav.value_id for rav in rows_appliesToValueIds if int(rav.parent_id) == row_id],
            excluded_product_ids=[rep.product_id for rep in rows_excludedProductIds if int(rep.parent_id) == row_id],
            applicable_payment_methods=r.applicable_payment_methods,
        )

    async def _fetch_children(self, session, ids: List[int]):
        if not ids:
            return [], [], [], [], [], []

        # Use parameterized IN clause to prevent SQL injection
        id_params = {f"cid_{i}": int(id_) for i, id_ in enumerate(ids)}
        placeholders = ", ".join(f":cid_{i}" for i in range(len(ids)))

        rows_quantityTiers = (await session.execute(
            text(f"SELECT parent_id, min_qty, discount_value FROM sj_coupon_quantity_tiers WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        rows_applicableRoles = (await session.execute(
            text(f"SELECT parent_id, role FROM sj_coupon_roles WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        rows_applicableUserIds = (await session.execute(
            text(f"SELECT parent_id, user_id FROM sj_coupon_users WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        rows_applicableCategories = (await session.execute(
            text(f"SELECT parent_id, category FROM sj_coupon_categories WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        rows_appliesToValueIds = (await session.execute(
            text(f"SELECT parent_id, value_id FROM sj_coupon_applies_to_values WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        rows_excludedProductIds = (await session.execute(
            text(f"SELECT parent_id, product_id FROM sj_coupon_excluded_products WHERE parent_id IN ({placeholders})"),
            id_params,
        )).fetchall()

        return (
            rows_quantityTiers,
            rows_applicableRoles,
            rows_applicableUserIds,
            rows_applicableCategories,
            rows_appliesToValueIds,
            rows_excludedProductIds,
        )

    async def _replace_user_usages(self, session, coupon_id: int, items: List[CouponUserUsageInternal]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_user_usages WHERE parent_id = :id"), {"id": coupon_id})
        for item in items:
            p = {"id": coupon_id, "v0": item.user_id, "v1": item.usage_count}
            await session.execute(
                text("INSERT INTO sj_coupon_user_usages (parent_id, user_id, usage_count) VALUES (:id, :v0, :v1) ON DUPLICATE KEY UPDATE usage_count = :v1"),
                p,
            )

    async def _replace_quantity_tiers(self, session, coupon_id: int, items: List[CouponQuantityTierInternal]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_quantity_tiers WHERE parent_id = :id"), {"id": coupon_id})
        for item in items:
            p = {"id": coupon_id, "v0": item.min_quantity, "v1": item.discount_value}
            await session.execute(
                text("INSERT INTO sj_coupon_quantity_tiers (parent_id, min_qty, discount_value) VALUES (:id, :v0, :v1)"),
                p,
            )

    async def _replace_roles(self, session, coupon_id: int, roles: List[str]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_roles WHERE parent_id = :id"), {"id": coupon_id})
        for role in roles:
            await session.execute(text("INSERT INTO sj_coupon_roles (parent_id, role) VALUES (:id, :v)"), {"id": coupon_id, "v": role})

    async def _replace_users(self, session, coupon_id: int, user_ids: List[str]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_users WHERE parent_id = :id"), {"id": coupon_id})
        for uid in user_ids:
            await session.execute(text("INSERT INTO sj_coupon_users (parent_id, user_id) VALUES (:id, :v)"), {"id": coupon_id, "v": uid})

    async def _replace_categories(self, session, coupon_id: int, categories: List[str]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_categories WHERE parent_id = :id"), {"id": coupon_id})
        for cat in categories:
            await session.execute(text("INSERT INTO sj_coupon_categories (parent_id, category) VALUES (:id, :v)"), {"id": coupon_id, "v": cat})

    async def _replace_applies_to_values(self, session, coupon_id: int, values: List[str]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_applies_to_values WHERE parent_id = :id"), {"id": coupon_id})
        for val in values:
            await session.execute(text("INSERT INTO sj_coupon_applies_to_values (parent_id, value_id) VALUES (:id, :v)"), {"id": coupon_id, "v": val})

    async def _replace_excluded_products(self, session, coupon_id: int, product_ids: List[str]) -> None:
        await session.execute(text("DELETE FROM sj_coupon_excluded_products WHERE parent_id = :id"), {"id": coupon_id})
        for pid in product_ids:
            await session.execute(text("INSERT INTO sj_coupon_excluded_products (parent_id, product_id) VALUES (:id, :v)"), {"id": coupon_id, "v": pid})
