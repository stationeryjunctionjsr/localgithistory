from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CouponInternal
from app.models.daos_flat import CouponInternalCreate, CouponInternalUpdate

def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _parse_dt(dt_val):
    if isinstance(dt_val, str):
        if dt_val.endswith("Z"):
            dt_val = dt_val[:-1] + "+00:00"
        dt_val = dt_val.replace("+00:00+00:00", "+00:00")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_val)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            pass
    return dt_val

class MySQLCouponsDAO:
    def __init__(self):
        self.table_name = "sj_coupons"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional['CouponInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['CouponInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'code': 'code', 'discount_type': 'discount_type', 'discount_value': 'discount_value', 'min_purchase_amount': 'min_order_value', 'usage_limit': 'max_uses', 'used_count': 'used_count', 'valid_from': 'start_date', 'valid_until': 'end_date', 'is_active': 'is_active', 'isActive': 'is_active', 'type_of_discount': 'type_of_discount', 'typeOfDiscount': 'type_of_discount', 'method': 'method', 'min_requirement_type': 'min_requirement_type', 'min_quantity_of_eligible_items': 'min_quantity_of_eligible_items', 'max_discount_amount': 'max_discount_amount', 'applies_to_type': 'applies_to_type'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map[k] if k in query_map else k
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List['CouponInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'code': 'code', 'discount_type': 'discount_type', 'discount_value': 'discount_value', 'min_purchase_amount': 'min_order_value', 'usage_limit': 'max_uses', 'used_count': 'used_count', 'valid_from': 'start_date', 'valid_until': 'end_date', 'is_active': 'is_active', 'isActive': 'is_active', 'type_of_discount': 'type_of_discount', 'typeOfDiscount': 'type_of_discount', 'method': 'method', 'min_requirement_type': 'min_requirement_type', 'min_quantity_of_eligible_items': 'min_quantity_of_eligible_items', 'max_discount_amount': 'max_discount_amount', 'applies_to_type': 'applies_to_type'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map[k] if k in query_map else k
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: 'CouponsInternalCreate') -> 'CouponInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

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
            params["s_validFrom"] = _parse_dt(data.valid_from)

        if data.valid_until is not None:
            cols.append("end_date")
            vals.append(":s_validUntil")
            params["s_validUntil"] = _parse_dt(data.valid_until)

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

        if data.displayId is not None:
            cols.append("display_id")
            vals.append(":s_displayId")
            params["s_displayId"] = data.displayId

        if data.buyXGetYCustomerGetsAppliesToValueIds is not None:
            cols.append("bxgy_applies_to_ids")
            vals.append(":s_bxgy_applies_to_ids")
            params["s_bxgy_applies_to_ids"] = json.dumps(data.buyXGetYCustomerGetsAppliesToValueIds)

        if data.buyXGetYCustomerGetsDiscountType is not None:
            cols.append("bxgy_discount_type")
            vals.append(":s_bxgy_discount_type")
            params["s_bxgy_discount_type"] = data.buyXGetYCustomerGetsDiscountType

        if data.buyXGetYCustomerGetsDiscountValue is not None:
            cols.append("bxgy_discount_value")
            vals.append(":s_bxgy_discount_value")
            params["s_bxgy_discount_value"] = data.buyXGetYCustomerGetsDiscountValue

        if data.applicableItemType is not None:
            cols.append("applicable_item_type")
            vals.append(":s_applicable_item_type")
            params["s_applicable_item_type"] = data.applicableItemType

        if data.coupon_mode is not None:
            cols.append("coupon_mode")
            vals.append(":s_coupon_mode")
            params["s_coupon_mode"] = data.coupon_mode

        if data.max_usage_per_user is not None:
            cols.append("max_usage_per_user")
            vals.append(":s_max_usage_per_user")
            params["s_max_usage_per_user"] = data.max_usage_per_user

        if data.userBehavior is not None:
            cols.append("user_behavior")
            vals.append(":s_user_behavior")
            params["s_user_behavior"] = data.userBehavior

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'CouponsInternalUpdate') -> 'CouponInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.code is not None:
            updates.append("code = :s_code")
            params["s_code"] = data.code

        if data.discount_type is not None:
            updates.append("discount_type = :s_discountType")
            params["s_discountType"] = data.discount_type

        if data.discount_value is not None:
            updates.append("discount_value = :s_discountValue")
            params["s_discountValue"] = data.discount_value

        if data.min_purchase_amount is not None:
            updates.append("min_order_value = :s_minOrderValue")
            params["s_minOrderValue"] = data.min_purchase_amount

        if data.usage_limit is not None:
            updates.append("max_uses = :s_maxUses")
            params["s_maxUses"] = data.usage_limit

        if data.used_count is not None:
            updates.append("used_count = :s_usedCount")
            params["s_usedCount"] = data.used_count

        if data.valid_from is not None:
            updates.append("start_date = :s_validFrom")
            params["s_validFrom"] = _parse_dt(data.valid_from)

        if data.valid_until is not None:
            updates.append("end_date = :s_validUntil")
            params["s_validUntil"] = _parse_dt(data.valid_until)

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = data.is_active

        if data.type_of_discount is not None:
            updates.append("type_of_discount = :s_typeOfDiscount")
            params["s_typeOfDiscount"] = data.type_of_discount

        if data.method is not None:
            updates.append("method = :s_method")
            params["s_method"] = data.method

        if data.min_requirement_type is not None:
            updates.append("min_requirement_type = :s_minRequirementType")
            params["s_minRequirementType"] = data.min_requirement_type

        if data.min_quantity_of_eligible_items is not None:
            updates.append("min_quantity_of_eligible_items = :s_minQuantityOfEligibleItems")
            params["s_minQuantityOfEligibleItems"] = data.min_quantity_of_eligible_items

        if data.max_discount_amount is not None:
            updates.append("max_discount_amount = :s_maxDiscountAmount")
            params["s_maxDiscountAmount"] = data.max_discount_amount

        if data.applies_to_type is not None:
            updates.append("applies_to_type = :s_appliesToType")
            params["s_appliesToType"] = data.applies_to_type

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:

            await session.execute(text(f"DELETE FROM sj_coupon_quantity_tiers WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_coupon_roles WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_coupon_users WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_coupon_categories WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_coupon_applies_to_values WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_coupon_excluded_products WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> 'CouponInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'CouponInternal':
        obj = CouponInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_quantityTiers = text(f"SELECT parent_id, min_qty, discount_value FROM sj_coupon_quantity_tiers WHERE parent_id IN ({id_list})")
        res_quantityTiers = await session.execute(q_quantityTiers)
        rows_quantityTiers = res_quantityTiers.fetchall()

        for r in rows_quantityTiers:
            if "quantity_tiers" not in c_map[r.parent_id]:
                c_map[r.parent_id]["quantity_tiers"] = []
            obj = {}

            obj["min_quantity"] = r[1]
            obj["discount_value"] = r[2]
            c_map[r.parent_id]["quantity_tiers"].append(obj)

        q_applicableRoles = text(f"SELECT parent_id, role FROM sj_coupon_roles WHERE parent_id IN ({id_list})")
        res_applicableRoles = await session.execute(q_applicableRoles)
        rows_applicableRoles = res_applicableRoles.fetchall()

        for r in rows_applicableRoles:
            if "applicable_roles" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applicable_roles"] = []
            c_map[r.parent_id]["applicable_roles"].append(r[1])

        q_applicableUserIds = text(f"SELECT parent_id, user_id FROM sj_coupon_users WHERE parent_id IN ({id_list})")
        res_applicableUserIds = await session.execute(q_applicableUserIds)
        rows_applicableUserIds = res_applicableUserIds.fetchall()

        for r in rows_applicableUserIds:
            if "applicable_user_ids" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applicable_user_ids"] = []
            c_map[r.parent_id]["applicable_user_ids"].append(r[1])

        q_applicableCategories = text(f"SELECT parent_id, category FROM sj_coupon_categories WHERE parent_id IN ({id_list})")
        res_applicableCategories = await session.execute(q_applicableCategories)
        rows_applicableCategories = res_applicableCategories.fetchall()

        for r in rows_applicableCategories:
            if "applicable_categories" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applicable_categories"] = []
            c_map[r.parent_id]["applicable_categories"].append(r[1])

        q_appliesToValueIds = text(f"SELECT parent_id, value_id FROM sj_coupon_applies_to_values WHERE parent_id IN ({id_list})")
        res_appliesToValueIds = await session.execute(q_appliesToValueIds)
        rows_appliesToValueIds = res_appliesToValueIds.fetchall()

        for r in rows_appliesToValueIds:
            if "applies_to_value_ids" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applies_to_value_ids"] = []
            c_map[r.parent_id]["applies_to_value_ids"].append(r[1])

        q_excludedProductIds = text(f"SELECT parent_id, product_id FROM sj_coupon_excluded_products WHERE parent_id IN ({id_list})")
        res_excludedProductIds = await session.execute(q_excludedProductIds)
        rows_excludedProductIds = res_excludedProductIds.fetchall()

        for r in rows_excludedProductIds:
            if "excluded_product_ids" not in c_map[r.parent_id]:
                c_map[r.parent_id]["excluded_product_ids"] = []
            c_map[r.parent_id]["excluded_product_ids"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):


        if data.user_usages is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_user_usages WHERE parent_id = :id"), {"id": row_id})
            child_list = data.user_usages or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}
                    p["v0"] = item.user_id
                    p["v1"] = item.usage_count
                    await session.execute(text(f"INSERT INTO sj_coupon_user_usages (parent_id, user_id, usage_count) VALUES (:id, :v0, :v1) ON DUPLICATE KEY UPDATE usage_count = :v1"), p)

        if data.quantity_tiers is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_quantity_tiers WHERE parent_id = :id"), {"id": row_id})
            child_list = data.quantity_tiers or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.min_quantity
                    p["v1"] = item.discount_value
                    await session.execute(text(f"INSERT INTO sj_coupon_quantity_tiers (parent_id, min_qty, discount_value) VALUES (:id, :v0, :v1)"), p)

        if data.applicable_roles is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_roles WHERE parent_id = :id"), {"id": row_id})
            child_list = data.applicable_roles or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_coupon_roles (parent_id, role) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.applicable_user_ids is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_users WHERE parent_id = :id"), {"id": row_id})
            child_list = data.applicable_user_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_coupon_users (parent_id, user_id) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.applicable_categories is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_categories WHERE parent_id = :id"), {"id": row_id})
            child_list = data.applicable_categories or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_coupon_categories (parent_id, category) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.applies_to_value_ids is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_applies_to_values WHERE parent_id = :id"), {"id": row_id})
            child_list = data.applies_to_value_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_coupon_applies_to_values (parent_id, value_id) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.excluded_product_ids is not None:
            await session.execute(text(f"DELETE FROM sj_coupon_excluded_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.excluded_product_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_coupon_excluded_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
