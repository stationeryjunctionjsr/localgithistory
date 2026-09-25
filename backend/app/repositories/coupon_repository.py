from app.models.schemas import CouponUpdate
from app.models.daos_flat import CouponInternalUpdate
from typing import Any
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger
from app.models.schemas import BxGyEvaluationResponse, CouponValidationResponse, CouponValidationDetail


class OverlapConflictError(ValueError):
    def __init__(self, overlap_data: 'CouponOverlapData'):
        self.overlap_data = overlap_data
        super().__init__("Similar discount already exists for overlapping products")


class CouponRepository:
    def __init__(self):
        self.storage = get_storage("coupons")
        self._category_storage = get_storage("categories")
        self._brand_storage = get_storage("brands")
        self._collection_storage = get_storage("collections")
        self._active_automatic_discounts_cache = None
        self._active_automatic_discounts_cache_time = None
        self._active_coupons_cache = None
        self._active_coupons_cache_time = None
        self._categories_map = None
        self._categories_map_time = None
        self._brands_map = None
        self._brands_map_time = None
        self._collections_map = None
        self._collections_map_time = None

    def invalidate_cache(self) -> None:
        """Invalidate the automatic discounts cache and category/brand/collection maps"""
        self._active_automatic_discounts_cache = None
        self._active_automatic_discounts_cache_time = None
        self._active_coupons_cache = None
        self._active_coupons_cache_time = None
        self._categories_map = None
        self._categories_map_time = None
        self._brands_map = None
        self._brands_map_time = None
        self._collections_map = None
        self._collections_map_time = None
        logger.info("CouponRepository cache invalidated")

    async def _get_category_name(self, cid: str) -> Optional[str]:
        now = datetime.now(timezone.utc)
        if (
            self._categories_map is None
            or not self._categories_map_time
            or (now - self._categories_map_time).total_seconds() > 60
        ):
            cats = await self._category_storage.findAll()
            self._categories_map = {str(c.id): (c.name if c.name is not None else "") for c in cats if "_id" in c}
            self._categories_map_time = now
        return (self._categories_map[str(cid)] if str(cid) in self._categories_map else None)

    async def _get_brand_name(self, bid: str) -> Optional[str]:
        now = datetime.now(timezone.utc)
        if self._brands_map is None or not self._brands_map_time or (now - self._brands_map_time).total_seconds() > 60:
            brands = await self._brand_storage.findAll()
            self._brands_map = {str(b.id): (b.name if b.name is not None else "") for b in brands if "_id" in b}
            self._brands_map_time = now
        return (self._brands_map[str(bid)] if str(bid) in self._brands_map else None)

    async def _get_collection_product_ids(self, cid: str) -> Optional[List[str]]:
        now = datetime.now(timezone.utc)
        if (
            self._collections_map is None
            or not self._collections_map_time
            or (now - self._collections_map_time).total_seconds() > 60
        ):
            cols = await self._collection_storage.findAll()
            self._collections_map = {
                str(c.id): [str(pid) for pid in (c.product_ids if c.product_ids is not None else [])] for c in cols if "_id" in c
            }
            self._collections_map_time = now
        return (self._collections_map[str(cid)] if str(cid) in self._collections_map else None)

    async def _calculate_bxgy_discount(
        self, coupon: Any, cart_items: List[Dict], product_repository, user_role: str, user_id: str
    ) -> Any:
        applicable_item_type = (coupon.applicable_item_type if coupon.applicable_item_type is not None else "units")
        x_required = int(coupon.min_quantity_of_eligible_items) if coupon.min_quantity_of_eligible_items is not None else None
        y_required = int(coupon.buy_x_get_y_customer_gets_quantity) if coupon.buy_x_get_y_customer_gets_quantity is not None else None

        # Batch-load all cart products upfront to avoid N+1 (one DB hit per item)
        cart_pids = [str(item.product or item.product_id) for item in cart_items if item.product or item.product_id]
        if cart_pids:
            products_list = await product_repository.findAll({"allowed_ids": cart_pids})
            product_map = {str(p.id): p for p in products_list if p.id}
        else:
            product_map = {}

        elements = []
        for idx, item in enumerate(cart_items):
            pid = str(item.product or item.product_id)
            product = (product_map[pid] if pid in product_map else None)
            if not product:
                continue
            qty = int(item.quantity) if item.quantity is not None else 0
            if qty <= 0:
                continue
            sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
            qty_per_case = int(product.quantityPerCase) if product.quantityPerCase is not None else 1

            item_total_price = product_repository.calculateTotalPrice(
                product, user_role, qty, sell_as_case=sell_as_case, user_id=user_id, ignore_auto_discount=True
            )

            if applicable_item_type == "cases":
                if not sell_as_case:
                    continue
                element_price = item_total_price / qty
                element_qty = qty
            else:
                element_qty = qty * qty_per_case if sell_as_case else qty
                element_price = item_total_price / element_qty

            is_bx_eligible = await self._product_eligible_async(
                product,
                (coupon.applies_to_type if coupon.applies_to_type is not None else "all"),
                (coupon.applies_to_value_ids if coupon.applies_to_value_ids is not None else None),
                (coupon.excluded_product_ids if coupon.excluded_product_ids is not None else None),
            )
            is_gy_eligible = await self._product_eligible_async(
                product,
                (coupon.buyXGetYCustomerGetsapplies_to_type if coupon.buyXGetYCustomerGetsapplies_to_type is not None else "all"),
                (coupon.buyXGetYCustomerGetsapplies_to_value_ids if coupon.buyXGetYCustomerGetsapplies_to_value_ids is not None else None),
                (coupon.excluded_product_ids if coupon.excluded_product_ids is not None else None),
            )
            for _ in range(element_qty):
                elements.append(
                    {
                        "idx": idx,
                        "pid": pid,
                        "price": element_price,
                        "is_bx": is_bx_eligible,
                        "is_gy": is_gy_eligible,
                        "product": product,
                    }
                )

        bx_candidates = [e for e in elements if e["is_bx"]]
        bx_candidates.sort(key=lambda x: x["price"], reverse=True)
        if len(bx_candidates) < x_required:
            return BxGyEvaluationResponse(discount=0.0, itemDiscounts={})

        bx_allocated = bx_candidates[:x_required]
        bx_ids = {id(e) for e in bx_allocated}

        gy_candidates = [e for e in elements if e["is_gy"] and id(e) not in bx_ids]
        gy_candidates.sort(key=lambda x: x["price"], reverse=True)
        gy_allocated = gy_candidates[:y_required]
        gy_ids = {id(e) for e in gy_allocated}

        if not gy_allocated:
            return BxGyEvaluationResponse(discount=0.0, itemDiscounts={})

        applicable_auto = await self.get_applicable_automatic_product_discounts(user_role, user_id)
        best_auto_per_product = {}
        for e in elements:
            pid = e["pid"]
            if pid not in best_auto_per_product:
                max_d = 0.0
                for c in applicable_auto:
                    if await self._product_eligible_async(
                        e["product"],
                        (c.applies_to_type if c.applies_to_type is not None else "all"),
                        c.applies_to_value_ids,
                        c.excluded_product_ids,
                    ):
                        d = (
                            (e["price"] * c.discount_value) / 100
                            if c.discount_type == "percentage"
                            else c.discount_value
                        )
                        if d > max_d:
                            max_d = min(d, e["price"])
                best_auto_per_product[pid] = max_d

        gy_discount_type = (coupon.buyXGetYCustomerGetsdiscount_type if coupon.buyXGetYCustomerGetsdiscount_type is not None else "percentage")
        gy_discount_value = float(coupon.buy_x_get_y_customer_gets_discount_value) if coupon.buy_x_get_y_customer_gets_discount_value is not None else 0.0

        gy_discount_amount = 0.0
        gy_element_discounts = []
        for e in gy_allocated:
            d = 0.0
            if gy_discount_type == "percentage":
                d = (e["price"] * gy_discount_value) / 100
            elif gy_discount_type == "amount_off":
                d = gy_discount_value
            elif gy_discount_type == "free":
                d = e["price"]
            d = min(d, e["price"])
            gy_discount_amount += d
            gy_element_discounts.append(d)

        fallback_discount_amount = sum(best_auto_per_product[e["pid"]] for e in bx_allocated + gy_allocated)

        total_discount = 0.0
        item_discounts = {}

        bxgy_item_indices = []
        if gy_discount_amount > fallback_discount_amount:
            bxgy_item_indices = list({e["idx"] for e in bx_allocated + gy_allocated})
            # Distribute gy_discount_amount across the entire BXGY set proportionally to their prices
            bxgy_set = bx_allocated + gy_allocated
            total_bxgy_price = sum(e["price"] for e in bxgy_set)

            for e in bxgy_set:
                d = gy_discount_amount * (e["price"] / total_bxgy_price) if total_bxgy_price > 0 else 0.0
                item_discounts[e["idx"]] = (item_discounts[e["idx"]] if e["idx"] in item_discounts else 0.0) + d
                total_discount += d
            for e in elements:
                if id(e) not in bx_ids and id(e) not in gy_ids:
                    d = best_auto_per_product[e["pid"]]
                    if d > 0:
                        item_discounts[e["idx"]] = (item_discounts[e["idx"]] if e["idx"] in item_discounts else 0.0) + d
                        total_discount += d
        else:
            for e in elements:
                d = best_auto_per_product[e["pid"]]
                if d > 0:
                    item_discounts[e["idx"]] = (item_discounts[e["idx"]] if e["idx"] in item_discounts else 0.0) + d
                    total_discount += d

        return BxGyEvaluationResponse(discount=total_discount, itemDiscounts=item_discounts, bxgyItemIndices=bxgy_item_indices)

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findByCode(self, code: str):
        if not code or not str(code).strip():
            return None
        return await self.storage.findOne({"code": code.upper()})

    async def _product_eligible_async(
        self,
        product: Any,
        applies_to_type: str,
        applies_to_value_ids: Optional[List[str]],
        excluded_product_ids: Optional[List[str]] = None,
    ) -> bool:
        pid = str(product.id if product.id is not None else product.id)
        
        if excluded_product_ids and pid in [str(x) for x in excluded_product_ids]:
            return False
        if not applies_to_value_ids:
            return applies_to_type == "all"
        if applies_to_type == "all":
            return True
        if applies_to_type == "categories":
            cat_name = (product.category or "").strip()
            if not cat_name:
                return False
            for cid in applies_to_value_ids:
                cat_name_cached = await self._get_category_name(cid)
                if cat_name_cached and cat_name_cached.strip() == cat_name:
                    return True
            return False
        if applies_to_type == "subCategories":
            sub = (product.subCategory or "").strip()
            return sub in applies_to_value_ids if sub else False
        if applies_to_type == "brands":
            brand_name = (product.brand or "").strip()
            if not brand_name:
                return False
            for bid in applies_to_value_ids:
                brand_name_cached = await self._get_brand_name(bid)
                if brand_name_cached and brand_name_cached.strip() == brand_name:
                    return True
            return False
        if applies_to_type == "collections":
            if not pid:
                return False
            for cid in applies_to_value_ids:
                product_ids_cached = await self._get_collection_product_ids(cid)
                if product_ids_cached and pid in product_ids_cached:
                    return True
            return False
        if applies_to_type == "products":
            return pid in [str(x) for x in applies_to_value_ids]
        return False

    async def _bundle_eligible_async(
        self,
        bundle: Any,
        applies_to_type: str,
        applies_to_value_ids: Optional[List[str]],
        excluded_product_ids: Optional[List[str]] = None,
    ) -> bool:
        """Determines if a bundle is eligible for a discount scheme."""
        bid = str(bundle.id if bundle.id is not None else bundle.id)
        
        if excluded_product_ids and bid in [str(x) for x in excluded_product_ids]:
            return False
            
        if applies_to_type == "all":
            return True
        elif applies_to_type == "bundles":
            if not applies_to_value_ids:
                return True
            return bid in [str(x) for x in applies_to_value_ids]
        # Bundles don't inherently belong to collections, subcategories, or products
        return False



    async def _user_matches_behavior(
        self,
        user_id: str,
        behavior: Optional[str],
        user_orders: Optional[List[Dict]] = None,
        has_app: Optional[bool] = None,
        user_behavior_cache: Optional[Dict] = None,
    ) -> bool:
        """Check if user matches discount user_behavior. For 'registered*' consider all users; for 'downloaded*' only app users."""
        if not behavior or behavior == "none":
            return True

        if user_behavior_cache is not None:
            cache_key = (user_id, behavior)
            if cache_key in user_behavior_cache:
                return user_behavior_cache[cache_key]

        async def evaluate():
            # Support multiple comma-separated behaviors / segments
            behaviors = [b.strip() for b in behavior.split(",") if b.strip()]
            matched_any = False
            for single_behavior in behaviors:
                if single_behavior.startswith("segment_"):
                    segment_id = single_behavior[len("segment_") :]
                    from app.repositories.customer_segments_repository import customer_segments_repository

                    segment = await customer_segments_repository.get_by_id(segment_id)
                    if segment and segment.userIds:
                        if str(user_id) in [str(x) for x in segment.userIds]:
                            matched_any = True
                            break
                else:
                    nonlocal user_orders
                    if user_orders is None:
                        from app.repositories.order_repository import order_repository

                        user_orders = await order_repository.findAll({"user": str(user_id)})

                    order_count = len(user_orders)

                    reference_date = datetime.now(timezone.utc)
                    three_months_ago = reference_date - timedelta(days=90)

                    recent_count = 0
                    for o in user_orders:
                        c_at_str = (o["createdAt"] if "createdAt" in o else None)
                        if not c_at_str or not isinstance(c_at_str, str):
                            continue
                        try:
                            c_at = datetime.fromisoformat(c_at_str.replace("Z", "+00:00"))
                            if c_at.tzinfo:
                                c_at = c_at.replace(tzinfo=None)
                            if three_months_ago <= c_at <= reference_date:
                                recent_count += 1
                        except (ValueError, TypeError, AttributeError):
                            logger.warning("Coupon eligibility: could not parse order createdAt %r; skipping.", c_at_str, exc_info=True)
                            continue

                    is_registered = True  # we're already in a flow with user_id

                    nonlocal has_app
                    if has_app is None:
                        has_app = False
                        try:
                            device_storage = get_storage("deviceSubscriptions")
                            devices = await device_storage.findAll({"userId": str(user_id)})
                            has_app = len(devices) > 0
                        except Exception:
                            logger.exception("Error checking for app usage for user")

                    if single_behavior == "registered_no_order" and is_registered and order_count == 0:
                        matched_any = True
                        break
                    elif single_behavior == "registered_one_order" and is_registered and order_count == 1:
                        matched_any = True
                        break
                    elif single_behavior == "regular_registered" and is_registered and recent_count >= 12:
                        matched_any = True
                        break
                    elif single_behavior == "registered_irregular" and is_registered and 3 < recent_count <= 9:
                        matched_any = True
                        break
                    elif single_behavior == "downloaded_no_order" and has_app and order_count == 0:
                        matched_any = True
                        break
                    elif single_behavior == "downloaded_one_order" and has_app and order_count == 1:
                        matched_any = True
                        break
                    elif single_behavior == "regular_app_user" and has_app and recent_count >= 12:
                        matched_any = True
                        break
                    elif single_behavior == "downloaded_irregular" and has_app and 3 < recent_count <= 9:
                        matched_any = True
                        break
            return matched_any

        result = await evaluate()
        if user_behavior_cache is not None:
            user_behavior_cache[cache_key] = result
        return result

    async def create(self, coupon_data: 'CouponInternalCreate'):
        method = (coupon_data.method if coupon_data.method is not None else "discount_code")
        code = coupon_data.code or ""
        if method == "discount_code" and code:
            existing = await self.findByCode(code)
            if existing:
                raise ValueError("Discount code already exists")
            code = code.upper()
        elif method == "automatic":
            code = None  # no code for automatic

        applicable_roles = (coupon_data.applicable_roles if coupon_data.applicable_roles is not None else ["customer"])
        prefix = "DISC-WH-" if "wholesaler" in applicable_roles else "DISC-RT-"

        # In simple array/json memory we can just filter
        # But motor query logic isn't always fully deterministic here if implemented purely as find
        # Let's get all coupons and manually find max to ensure safety across DBs
        all_coupons = await self.storage.findAll({})
        max_num = 0
        for doc in all_coupons:
            did = doc.code or ""
            if did.startswith(prefix):
                try:
                    num = int(did[len(prefix) :])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        display_id = f"{prefix}{max_num + 1}"

        from app.models.daos_flat import CouponInternalCreate, CouponQuantityTierInternal
        
        qt_list = None
        if coupon_data.quantity_tiers is not None:
            qt_list = [CouponQuantityTierInternal(minQuantity=int(t.quantity), discount_value=float(t.discount)) for t in coupon_data.quantity_tiers]

        coupon = CouponInternalCreate(
            type_of_discount=(coupon_data.type_of_discount if coupon_data.type_of_discount is not None else "product_discount"),
            code=code,
            method=method,
            discount_type=(coupon_data.discount_type if coupon_data.discount_type is not None else "percentage"),
            discount_value=float(coupon_data.discount_value),
            min_order_value=float(coupon_data.min_purchase_amount),
            minRequirementType=(coupon_data.min_requirement_type if coupon_data.min_requirement_type is not None else "none"),
            minQuantityOfEligibleItems=int(coupon_data.min_quantity_of_eligible_items) if coupon_data.min_quantity_of_eligible_items is not None else None,
            max_discountAmount=float(coupon_data.max_discount_amount) if coupon_data.max_discount_amount else None,
            valid_from=(coupon_data.valid_from if coupon_data.valid_from is not None else datetime.now(timezone.utc).isoformat()),
            valid_until=coupon_data.valid_until,
            maxUses=int(coupon_data.usage_limit) if coupon_data.usage_limit else None,
            usedCount=0,
            is_active=(coupon_data.is_active if coupon_data.is_active is not None else True),
            applicable_roles=(coupon_data.applicable_roles if coupon_data.applicable_roles is not None else ["customer"]),
            applicable_user_ids=coupon_data.applicable_user_ids or [],
            applicableCategories=coupon_data.applicableCategories or [],
            applies_to_type=(coupon_data.applies_to_type if coupon_data.applies_to_type is not None else "all"),
applies_to_value_ids=coupon_data.applies_to_value_ids or [],
            excludedProductIds=coupon_data.excluded_product_ids or [],
            quantityTiers=qt_list,
            displayId=display_id,
            buyXGetYCustomerGetsapplies_to_value_ids=coupon_data.buyXGetYCustomerGetsapplies_to_value_ids or [],
            buyXGetYCustomerGetsdiscount_type=coupon_data.buyXGetYCustomerGetsdiscount_type,
            buy_x_get_y_customer_gets_discount_value=float(coupon_data.buy_x_get_y_customer_gets_discount_value) if coupon_data.buy_x_get_y_customer_gets_discount_value is not None else None,
            applicable_item_type=coupon_data.applicable_item_type or "units",
            couponMode=coupon_data.coupon_mode or "override",
            maxUsagePerUser=int(coupon_data.maxUsagePerUser) if coupon_data.maxUsagePerUser else None,
            user_behavior=coupon_data.user_behavior,
        )

        # Handle Overlap
        resolution = coupon_data.resolution
        force = (coupon_data.force if coupon_data.force is not None else False)

        if not force:
            overlap = await self.check_discount_overlap(coupon)
            if overlap:
                if resolution == "overwrite":
                    # Add exclusions to existing coupons
                    for detail in overlap["details"]:
                        existing_coupon = await self.findById(detail["couponId"])
                        if existing_coupon:
                            excl = set(existing_coupon.excluded_product_ids or [])
                            excl.update(detail["overlappingProductIds"])
                            await self.storage.update(detail["couponId"], CouponInternalUpdate(excludedProductIds=list(excl)))
                elif resolution == "retain":
                    # Add exclusions to current coupon
                    excl = set((coupon.excluded_product_ids if coupon.excluded_product_ids is not None else None) or [])
                    pids_to_exclude = set().union(*[set(d["overlappingProductIds"]) for d in overlap["details"]])

                    # Check if all targeted products are excluded/covered
                    targeted_pids = await self._get_affected_product_ids(coupon)
                    if targeted_pids.issubset(pids_to_exclude):
                        raise ValueError(
                            "Discount not created because all targeted products are covered by retained earlier discounts"
                        )

                    excl.update(list(pids_to_exclude))
                    coupon.excluded_product_ids = list(excl)
                else:
                    raise OverlapConflictError(overlap)

        res = await self.storage.create(coupon)
        self.invalidate_cache()
        return res

    async def update(self, id: str, update_data: 'CouponInternalUpdate'):
        from app.models.daos_flat import CouponInternalUpdate, CouponQuantityTierInternal
        from app.models.schemas import Coupon, CouponValidationResponse, BxGyEvaluationResponseUpdate
        
        # Coerce to CouponUpdate to avoid getattr/hasattr dynamic checking
        if not isinstance(update_data, CouponUpdate):
            update_data = CouponUpdate.model_validate(update_data)
            
        if update_data.code:
            existing = await self.findByCode(update_data.code)
            if existing and existing.id != id:
                raise ValueError("Discount code already in use")
            update_data.code = update_data.code.upper()
            
        if update_data.method == "automatic":
            update_data.code = None
        
        internal_update = CouponInternalUpdate()
        
        # Map fields explicitly
        if 'type_of_discount' in update_data.model_fields_set: internal_update.type_of_discount = update_data.type_of_discount
        if 'code' in update_data.model_fields_set: internal_update.code = update_data.code
        if 'method' in update_data.model_fields_set: internal_update.method = update_data.method
        if 'discount_type' in update_data.model_fields_set: internal_update.discount_type = update_data.discount_type
        if 'discount_value' in update_data.model_fields_set: internal_update.discount_value = update_data.discount_value
        
        if 'quantityTiers' in update_data.model_fields_set and update_data.quantity_tiers is not None:
            internal_update.quantity_tiers = [CouponQuantityTierInternal(minQuantity=int(t.quantity), discount_value=float(t.discount)) for t in update_data.quantity_tiers]
            
        if 'minPurchaseAmount' in update_data.model_fields_set and update_data.min_purchase_amount is not None:
            internal_update.min_order_value = float(update_data.min_purchase_amount)
            
        if 'usage_limit' in update_data.model_fields_set and update_data.usage_limit is not None:
            internal_update.maxUses = int(update_data.usage_limit)
            
        if 'minRequirementType' in update_data.model_fields_set: internal_update.min_requirement_type = update_data.min_requirement_type
        if 'minQuantityOfEligibleItems' in update_data.model_fields_set: internal_update.min_quantity_of_eligible_items = update_data.min_quantity_of_eligible_items
        if 'max_discountAmount' in update_data.model_fields_set: internal_update.max_discount_amount = update_data.max_discount_amount
        if 'valid_from' in update_data.model_fields_set: internal_update.valid_from = update_data.valid_from
        if 'valid_until' in update_data.model_fields_set: internal_update.valid_until = update_data.valid_until
        if 'is_active' in update_data.model_fields_set: internal_update.is_active = update_data.is_active
        if 'combinations' in update_data.model_fields_set: internal_update.combinations = update_data.combinations
        if 'appliesTo' in update_data.model_fields_set: internal_update.appliesTo = update_data.appliesTo
        if 'eligibleCategories' in update_data.model_fields_set: internal_update.eligibleCategories = update_data.eligibleCategories
        if 'eligibleSubCategories' in update_data.model_fields_set: internal_update.eligibleSubCategories = update_data.eligibleSubCategories
        if 'eligibleProducts' in update_data.model_fields_set: internal_update.eligibleProducts = update_data.eligibleProducts
        if 'eligibleSegments' in update_data.model_fields_set: internal_update.eligibleSegments = update_data.eligibleSegments
        if 'brands' in update_data.model_fields_set: internal_update.brands = update_data.brands

        res = await self.storage.update(id, internal_update)
        self.invalidate_cache()
        return res

    async def delete(self, id: str):
        res = await self.storage.delete(id)
        self.invalidate_cache()
        return res

    async def incrementUsage(self, id: str, user_id: str):
        """Atomically increment used_count for a coupon.

        Uses a single SQL UPDATE (used_count = used_count + 1) so concurrent
        checkouts with the same coupon code cannot race past the max_uses limit.
        """
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return None

        from sqlalchemy import text
        from app.config.database import get_async_session_factory
        factory = get_async_session_factory()
        if not factory:
            # No MySQL — best-effort fallback (single-process only, not race-safe)
            coupon = await self.findById(id)
            if not coupon:
                return None
            new_count = (coupon.usedCount if coupon.usedCount is not None else 0) + 1
            res = await self.storage.update(id, CouponInternalUpdate(usedCount=new_count))
            self.invalidate_cache()
            return res

        async with factory() as session:
            await session.execute(
                text(
                    "UPDATE sj_coupons "
                    "SET used_count = used_count + 1, updated_at = UTC_TIMESTAMP() "
                    "WHERE id = :id"
                ),
                {"id": pk},
            )
            
            # Upsert user usage atomically
            await session.execute(
                text("INSERT INTO sj_coupon_user_usages (parent_id, user_id, usage_count) VALUES (:id, :uid, 1) "
                     "ON DUPLICATE KEY UPDATE usage_count = usage_count + 1"),
                {"id": pk, "uid": user_id}
            )
            await session.commit()

        self.invalidate_cache()
        return await self.findById(id)


# ── MULTI-VM COUPON INCREMENT (commented out — already atomic at DB level) ───────
#
# The active incrementUsage() above uses a single atomic
#   UPDATE sj_coupons SET used_count = used_count + 1 WHERE id = :id
# This is a MySQL atomic write, safe across ALL workers on ALL VMs sharing the DB.
#
# HOW SINGLE-VM WORKS (active):
#   With uvicorn --workers 4, all 4 processes may hit this simultaneously.
#   MySQL guarantees that "used_count = used_count + 1" is evaluated and
#   committed atomically — no two processes can interleave their increments.
#
# IF OPTIMISTIC LOCKING IS EVER NEEDED (strict max_uses enforcement under extreme load):
#   Add a `version INT DEFAULT 0` column to sj_coupons.  Then retry on conflict:
#
# # async def increment_usage_optimistic(self, id: str, user_id: str, max_retries: int = 3):
# #     """Increment used_count using optimistic locking (version column).
# #     Retries up to max_retries times if another worker updated concurrently.
# #     Use when you need strict max_uses enforcement AND want explicit retry control.
# #     """
# #     pk = int(id) if str(id).isdigit() else None
# #     if pk is None:
# #         return None
# #     from sqlalchemy import text
# #     from app.config.database import get_async_session_factory
# #     factory = get_async_session_factory()
# #     for attempt in range(max_retries):
# #         async with factory() as session:
# #             row = await session.execute(
# #                 text("SELECT used_count, version FROM sj_coupons WHERE id = :id FOR UPDATE"),
# #                 {"id": pk},
# #             )
# #             r = row.fetchone()
# #             if not r:
# #                 return None
# #             result = await session.execute(
# #                 text(
# #                     "UPDATE sj_coupons "
# #                     "SET used_count = used_count + 1, version = version + 1, "
# #                     "    updated_at = UTC_TIMESTAMP() "
# #                     "WHERE id = :id AND version = :v"
# #                 ),
# #                 {"id": pk, "v": r.version},
# #             )
# #             await session.commit()
# #             if result.rowcount == 1:
# #                 self.invalidate_cache()
# #                 return await self.findById(id)
# #     raise RuntimeError(f"Could not increment coupon {id} after {max_retries} attempts")
#
# TO ACTIVATE:
#   1. Add migration: ALTER TABLE sj_coupons ADD COLUMN version INT NOT NULL DEFAULT 0;
#   2. Replace calls to incrementUsage() with increment_usage_optimistic().
#
# ─────────────────────────────────────────────────────────────────────────────────

    async def validateCoupon(
        self,
        code: str,
        user_role: str,
        purchase_amount: float,
        user_id: str,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        cart_items: Optional[List[Dict]] = None,
        product_repository=None,
        shipping_address: Optional[Dict] = None,
        shipping_charge: float = 0.0,
    ):
        """
        If cart_items and product_repository are provided, purchase_amount is ignored and
        eligible subtotal is computed from cart items that match appliesTo. Otherwise
        purchase_amount is used (backward compat).
        """
        coupon = await self.findByCode(code)

        if not coupon:
            return CouponValidationResponse(valid=False, message="Invalid coupon code")

        if not (coupon.is_active if coupon.is_active is not None else True):
            return CouponValidationResponse(valid=False, message="Discount is not active")

        now = datetime.now(timezone.utc)
        valid_from = coupon.start_date if isinstance(coupon.start_date, datetime) else datetime.fromisoformat(coupon.start_date.replace('Z', '+00:00'))
        if valid_from.tzinfo is None: valid_from = valid_from.replace(tzinfo=timezone.utc)
        valid_until = coupon.end_date if isinstance(coupon.end_date, datetime) else datetime.fromisoformat(coupon.end_date.replace('Z', '+00:00'))
        if valid_until.tzinfo is None: valid_until = valid_until.replace(tzinfo=timezone.utc)

        if now < valid_from:
            return CouponValidationResponse(valid=False, message="Discount is not yet valid")

        if now > valid_until:
            return CouponValidationResponse(valid=False, message="Discount has expired")

        if (coupon.maxUses if coupon.maxUses is not None else None) and (coupon.usedCount if coupon.usedCount is not None else 0) >= coupon.maxUses:
            return CouponValidationResponse(valid=False, message="Discount usage limit reached")

        if (coupon.maxUsagePerUser if coupon.maxUsagePerUser is not None else None):
            user_usages = coupon.userUsages or []
            usage_count = next((u.usageCount for u in user_usages if u.userId == user_id), 0)
            if usage_count >= coupon.maxUsagePerUser:
                return CouponValidationResponse(valid=False, message=f"You have reached the maximum usage limit ({coupon.maxUsagePerUser}) for this discount")

        if user_role not in (coupon.applicable_roles if coupon.applicable_roles is not None else []):
            return CouponValidationResponse(valid=False, message="Discount not applicable for your role")

        # Selective customers & User behavior segments check
        applicable_user_ids = (coupon.applicable_user_ids if coupon.applicable_user_ids is not None else None) or []
        user_behavior = (coupon.user_behavior if coupon.user_behavior is not None else None)
        has_specific_users = len(applicable_user_ids) > 0 or (user_behavior and user_behavior != "none")

        if has_specific_users:
            matches_selective = str(user_id) in [str(x) for x in applicable_user_ids]
            matches_behavior = (
                await self._user_matches_behavior(user_id, user_behavior)
                if (user_behavior and user_behavior != "none")
                else False
            )
            if not (matches_selective or matches_behavior):
                return CouponValidationResponse(valid=False, message="Discount not applicable for your account")

        applicable_payment_methods = coupon.applicablePaymentMethods
        if (
            applicable_payment_methods is not None
            and payment_method
            and payment_method.lower() not in [m.lower() for m in applicable_payment_methods]
        ):
            return CouponValidationResponse(valid=False, message=f"Discount not applicable for {payment_method.upper()} payment method")

        if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "shipping_discount":
            if not shipping_address:
                # Try to get from user
                from app.repositories.user_repository import user_repository

                user_record = await user_repository.findById(user_id)
                if user_record and (user_record["address"] if "address" in user_record else None):
                    shipping_address = (user_record["address"] if "address" in user_record else None)

            if shipping_address:
                pincode = (shipping_address["zipCode"] if "zipCode" in shipping_address else None) or (shipping_address["pincode"] if "pincode" in shipping_address else None)
                if not pincode:
                    return CouponValidationResponse(valid=False, message="Shipping address must include a pincode for this discount.")
                allowed_pincodes = (coupon.shippingPincodes if coupon.shippingPincodes is not None else None) or []
                if allowed_pincodes and str(pincode).strip() not in [str(p).strip() for p in allowed_pincodes]:
                    return CouponValidationResponse(valid=False, message=f"This shipping discount is not applicable for pincode {pincode}.")
            else:
                return CouponValidationResponse(valid=False, message="A shipping address is required to apply this shipping discount.")

        # Resolve purchase amount and eligible quantity from cart items (eligible only) or from argument
        purchase_amount_to_use = purchase_amount
        eligible_item_indices = None
        eligible_quantity = 0
        if cart_items and product_repository:
            eligible_item_indices = []
            applies_to_type = (coupon.applies_to_type if coupon.applies_to_type is not None else None) or "all"
            applies_to_ids = (coupon.applies_to_value_ids if coupon.applies_to_value_ids is not None else None) or []
            eligible_subtotal = 0.0
            for idx, item in enumerate(cart_items):
                product = await product_repository.findById(item.product or item.product_id)
                if not product:
                    continue
                if await self._product_eligible_async(
                    product,
                    applies_to_type,
                    applies_to_ids if applies_to_ids else None,
                    (coupon.excluded_product_ids if coupon.excluded_product_ids is not None else None),
                ):
                    qty = (item.quantity if item.quantity is not None else 0)
                    eligible_quantity += qty
                    sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
                    ignore_auto = (coupon.method if coupon.method is not None else None) == "discount_code" and (coupon.coupon_mode if coupon.coupon_mode is not None else None) == "override"
                    item_total = product_repository.calculateTotalPrice(
                        product,
                        user_role,
                        qty,
                        sell_as_case=sell_as_case,
                        user_id=user_id,
                        ignore_auto_discount=ignore_auto,
                    )
                    eligible_subtotal += item_total
                    eligible_item_indices.append(idx)
            purchase_amount_to_use = eligible_subtotal
        else:
            applicable_categories = (coupon.applicableCategories if coupon.applicableCategories is not None else [])
            if applicable_categories and category and category not in applicable_categories:
                return CouponValidationResponse(valid=False, message="Discount not applicable for this category")

        min_req = (coupon.min_requirement_type if coupon.min_requirement_type is not None else None) or "none"
        if min_req == "min_amount" and purchase_amount_to_use < (coupon.min_purchase_amount if coupon.min_purchase_amount is not None else 0):
            return CouponValidationResponse(valid=False, message=f"Minimum purchase amount of {coupon.min_purchase_amount} required (on eligible items)")
        if min_req == "min_quantity":
            min_qty = (coupon.min_quantity_of_eligible_items if coupon.min_quantity_of_eligible_items is not None else None) or 0
            if eligible_quantity < min_qty:
                return CouponValidationResponse(valid=False, message=f"Minimum quantity of {min_qty} eligible items required (you have {eligible_quantity} eligible in cart)")
            if not cart_items and min_qty > 0:
                return CouponValidationResponse(valid=False, message="Minimum quantity requirement cannot be validated without cart items")

        # Calculate discount on eligible amount only
        discount = 0.0
        item_discounts = None
        bxgy_item_indices = None
        if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "buy_x_get_y" and cart_items and product_repository:
            bxgy_res = await self._calculate_bxgy_discount(coupon, cart_items, product_repository, user_role, user_id)
            discount = bxgy_res.discount
            item_discounts = bxgy_res.item_discounts
            bxgy_item_indices = bxgy_res.bxgy_item_indices
        elif (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "shipping_discount":
            if coupon.discount_type == "percentage":
                discount = (shipping_charge * coupon.discount_value) / 100
                if (coupon.max_discount_amount if coupon.max_discount_amount is not None else None):
                    discount = min(discount, coupon.max_discount_amount)
            else:
                discount = coupon.discount_value
            discount = min(discount, shipping_charge)
        else:
            if coupon.discount_type == "percentage":
                discount = (purchase_amount_to_use * coupon.discount_value) / 100
                if (coupon.max_discount_amount if coupon.max_discount_amount is not None else None):
                    discount = min(discount, coupon.max_discount_amount)
            else:
                if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "product_discount":
                    discount = eligible_quantity * coupon.discount_value
                else:
                    discount = coupon.discount_value

        return CouponValidationResponse(
            valid=True,
            coupon=CouponValidationDetail(
                code=coupon.code,
                discount_type=coupon.discount_type,
                discount_value=coupon.discount_value,
                id=str(coupon.id) if coupon.id else None,
                method=coupon.method,
                couponMode=coupon.coupon_mode or "override",
                type_of_discount=coupon.type_of_discount
            ),
            discount=round(discount, 2),
            eligibleItemIndices=eligible_item_indices,
            itemDiscounts=item_discounts,
            bxgyItemIndices=bxgy_item_indices,
        )

    async def find_applicable_automatic_discounts(
        self,
        user_id: str,
        user_role: str,
        cart_items: List[Dict],
        product_repository,
        payment_method: Optional[str] = None,
        shipping_address: Optional[Dict] = None,
        shipping_charge: float = 0.0,
    ) -> List[Any]:
        """Find active automatic discounts that match user and cart. Returns list of { coupon, discount, eligibleItemIndices }."""
        now = datetime.now(timezone.utc)
        all_coupons = await self.storage.findAll({"method": "automatic", "is_active": True})
        results = []
        for coupon in all_coupons:
            try:
                if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "product_discount":
                    continue
                valid_from = coupon.start_date if isinstance(coupon.start_date, datetime) else datetime.fromisoformat(coupon.start_date.replace('Z', '+00:00'))
                if valid_from.tzinfo is None: valid_from = valid_from.replace(tzinfo=timezone.utc)
                valid_until = coupon.end_date if isinstance(coupon.end_date, datetime) else datetime.fromisoformat(coupon.end_date.replace('Z', '+00:00'))
                if valid_until.tzinfo is None: valid_until = valid_until.replace(tzinfo=timezone.utc)
                if now < valid_from or now > valid_until:
                    continue
                if coupon.maxUses and (coupon.usedCount if coupon.usedCount is not None else 0) >= coupon.maxUses:
                    continue
                if user_role not in (coupon.applicable_roles if coupon.applicable_roles is not None else []):
                    continue
                applicable_user_ids = (coupon.applicable_user_ids if coupon.applicable_user_ids is not None else None) or []
                user_behavior = (coupon.user_behavior if coupon.user_behavior is not None else None)
                has_specific_users = len(applicable_user_ids) > 0 or (user_behavior and user_behavior != "none")

                if has_specific_users:
                    matches_selective = str(user_id) in [str(x) for x in applicable_user_ids]
                    matches_behavior = (
                        await self._user_matches_behavior(user_id, user_behavior)
                        if (user_behavior and user_behavior != "none")
                        else False
                    )
                    if not (matches_selective or matches_behavior):
                        continue
                if payment_method:
                    applicable_payment_methods = coupon.applicablePaymentMethods
                    if applicable_payment_methods is not None and payment_method.lower() not in [
                        m.lower() for m in applicable_payment_methods
                    ]:
                        continue

                if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "shipping_discount":
                    addr = shipping_address
                    if not addr:
                        from app.repositories.user_repository import user_repository

                        u = await user_repository.findById(user_id)
                        if u and u.address:
                            addr = u.address

                    if addr:
                        pincode = (addr["zipCode"] if "zipCode" in addr else None) or (addr["pincode"] if "pincode" in addr else None)
                        if not pincode:
                            continue
                        allowed_pincodes = (coupon.shippingPincodes if coupon.shippingPincodes is not None else None) or []
                        if allowed_pincodes and str(pincode).strip() not in [str(p).strip() for p in allowed_pincodes]:
                            continue
                    else:
                        continue
                # Compute eligible subtotal and quantity
                applies_to_type = (coupon.applies_to_type if coupon.applies_to_type is not None else None) or "all"
                applies_to_ids = (coupon.applies_to_value_ids if coupon.applies_to_value_ids is not None else None) or []
                eligible_subtotal = 0.0
                eligible_quantity = 0
                eligible_item_indices = []
                for idx, item in enumerate(cart_items):
                    product = await product_repository.findById(item.product or item.product_id)
                    if not product:
                        continue
                    if await self._product_eligible_async(
                        product,
                        applies_to_type,
                        applies_to_ids if applies_to_ids else None,
                        (coupon.excluded_product_ids if coupon.excluded_product_ids is not None else None),
                    ):
                        qty = (item.quantity if item.quantity is not None else 0)
                        eligible_quantity += qty
                        sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
                        item_total = product_repository.calculateTotalPrice(
                            product, user_role, qty, sell_as_case=sell_as_case, user_id=user_id
                        )
                        eligible_subtotal += item_total
                        eligible_item_indices.append(idx)
                min_req = (coupon.min_requirement_type if coupon.min_requirement_type is not None else None) or "none"
                if min_req == "min_amount" and eligible_subtotal < (coupon.min_purchase_amount if coupon.min_purchase_amount is not None else 0):
                    continue
                if min_req == "min_quantity":
                    min_qty = int(coupon.min_quantity_of_eligible_items) if coupon.min_quantity_of_eligible_items is not None else 0
                    if eligible_quantity < min_qty:
                        continue
                if (coupon.maxUsagePerUser if coupon.maxUsagePerUser is not None else None):
                    user_usages = coupon.userUsages or []
                    usage_count = next((u.usageCount for u in user_usages if u.userId == user_id), 0)
                    if usage_count >= coupon.maxUsagePerUser:
                        continue
                discount = 0.0
                item_discounts = None
                bxgy_item_indices = None
                if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "buy_x_get_y":
                    bxgy_res = await self._calculate_bxgy_discount(
                        coupon, cart_items, product_repository, user_role, user_id
                    )
                    discount = bxgy_res.discount
                    item_discounts = bxgy_res.item_discounts
                    bxgy_item_indices = bxgy_res.bxgy_item_indices
                elif (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "shipping_discount":
                    if coupon.discount_type == "percentage":
                        discount = (shipping_charge * coupon.discount_value) / 100
                        if (coupon.max_discount_amount if coupon.max_discount_amount is not None else None):
                            discount = min(discount, coupon.max_discount_amount)
                    else:
                        discount = coupon.discount_value
                    discount = min(discount, shipping_charge)
                else:
                    if coupon.discount_type == "percentage":
                        discount = (eligible_subtotal * coupon.discount_value) / 100
                        if (coupon.max_discount_amount if coupon.max_discount_amount is not None else None):
                            discount = min(discount, coupon.max_discount_amount)
                    else:
                        if (coupon.type_of_discount if coupon.type_of_discount is not None else None) == "product_discount":
                            discount = eligible_quantity * coupon.discount_value
                        else:
                            discount = coupon.discount_value
                results.append(
                    CouponValidationResponse(
                        valid=True,
                        coupon=CouponValidationDetail(
                            code=coupon.code,
                            discount_type=coupon.discount_type,
                            discount_value=coupon.discount_value,
                            id=str(coupon.id) if coupon.id else None,
                            method=coupon.method,
                            couponMode=coupon.coupon_mode or "override",
                            type_of_discount=coupon.type_of_discount
                        ),
                        discount=round(discount, 2),
                        eligibleItemIndices=eligible_item_indices,
                        itemDiscounts=item_discounts,
                        bxgyItemIndices=bxgy_item_indices,
                    )
                )
            except Exception:
                logger.warning("Coupon %r failed cart calculation; skipping.", getattr(coupon, 'id', '?'), exc_info=True)
                continue
        return results

    async def _get_affected_product_ids(self, coupon_data: 'CouponInternal') -> set:
        """Expand applies_to_type/ValueIds into a set of product IDs."""
        applies_to_type = coupon_data.applies_to_type or "all"
        applies_to_value_ids = coupon_data.applies_to_value_ids or []
        excluded_product_ids = set(str(x) for x in (coupon_data.excluded_product_ids or []))

        from app.repositories.product_repository import product_repository

        if not applies_to_value_ids and applies_to_type != "all":
            return set()

        # O(0) DB product query optimization for specific products list
        if applies_to_type == "products":
            return set(str(pid) for pid in applies_to_value_ids if str(pid) not in excluded_product_ids)

        # O(0) DB product query optimization for collections
        if applies_to_type == "collections" and applies_to_value_ids:
            eligible_collection_product_ids = set()
            for cid in applies_to_value_ids:
                col = await self._collection_storage.findById(cid)
                if col:
                    pids = (col["productIds"] if "productIds" in col else None) or []
                    for pid in pids:
                        eligible_collection_product_ids.add(str(pid))
            return set(pid for pid in eligible_collection_product_ids if pid not in excluded_product_ids)

        # Build query filters to load only matching products from database
        query = {"is_active": True}
        eligible_category_names = set()
        eligible_brand_names = set()

        if applies_to_type == "categories" and applies_to_value_ids:
            for cid in applies_to_value_ids:
                cat = await self._category_storage.findById(cid)
                if cat and (cat["name"] if "name" in cat else None):
                    eligible_category_names.add((cat["name"] if "name" in cat else None).strip())
            if eligible_category_names:
                query["categories"] = ",".join(eligible_category_names)
            else:
                return set()
        elif applies_to_type == "brands" and applies_to_value_ids:
            for bid in applies_to_value_ids:
                brand = await self._brand_storage.findById(bid)
                if brand and brand.name:
                    eligible_brand_names.add(brand.name.strip())
            if eligible_brand_names:
                query["brand"] = ",".join(eligible_brand_names)
            else:
                return set()
        elif applies_to_type == "subCategories" and applies_to_value_ids:
            if len(applies_to_value_ids) == 1:
                query["subCategory"] = applies_to_value_ids[0]

        # Fetch only filtered subset of products
        products = await product_repository.findAll(query)

        affected = set()
        for p in products:
            pid = str((p.id if p.id is not None else ""))
            if pid in excluded_product_ids:
                continue

            if applies_to_type == "all":
                affected.add(pid)
            elif applies_to_type == "categories":
                p_cat = (p.category or "").strip().lower()
                if p_cat and p_cat in {c.lower() for c in eligible_category_names}:
                    affected.add(pid)
            elif applies_to_type == "subCategories":
                p_sub = (p.subCategory or "").strip()
                if p_sub and p_sub in applies_to_value_ids:
                    affected.add(pid)
            elif applies_to_type == "brands":
                p_brand = (p.brand or "").strip().lower()
                if p_brand and p_brand in {b.lower() for b in eligible_brand_names}:
                    affected.add(pid)

        return affected

    async def check_discount_overlap(self, coupon_data: 'CouponInternal', exclude_coupon_id: Optional[str] = None):
        """Identify conflicting active coupons and return affected product count."""
        if not (coupon_data.is_active if coupon_data.is_active is not None else True):
            return None

        roles = coupon_data.applicable_roles or []
        all_coupons = await self.storage.findAll({"is_active": True})

        # Filter for same roles
        conflicting_candidates = [
            c
            for c in all_coupons
            if any(r in (c.applicable_roles or []) for r in roles) and str(c.id) != str(exclude_coupon_id)
        ]

        new_affected_ids = await self._get_affected_product_ids(coupon_data)
        type_of_discount = coupon_data.type_of_discount or "product_discount"

        if type_of_discount == "buy_x_get_y":
            gy_applies_to_type = (coupon_data.buyXGetYCustomerGetsapplies_to_type if coupon_data.buyXGetYCustomerGetsapplies_to_type is not None else "all")
            gy_applies_to_ids = coupon_data.buyXGetYCustomerGetsapplies_to_value_ids or []
            dummy_gy_coupon = {
                "applies_to_type": gy_applies_to_type,
                "applies_to_value_ids": gy_applies_to_ids,
                "excludedProductIds": coupon_data.excluded_product_ids,
            }
            gy_affected_ids = await self._get_affected_product_ids(dummy_gy_coupon)
            new_affected_ids = new_affected_ids.union(gy_affected_ids)

        if not new_affected_ids:
            return None

        applicable_item_type = coupon_data.applicable_item_type or "units"

        overlaps = []
        for c in conflicting_candidates:
            c_type = c.type_of_discount or "product_discount"
            if c_type != type_of_discount:
                continue

            is_bxgy = type_of_discount == "buy_x_get_y"
            c_affected_ids = await self._get_affected_product_ids(c)
            if is_bxgy:
                c_gy_applies_to_type = (c.buyXGetYCustomerGetsapplies_to_type if c.buyXGetYCustomerGetsapplies_to_type is not None else "all")
                c_gy_applies_to_ids = c.buyXGetYCustomerGetsapplies_to_value_ids or []
                c_dummy_gy = {
                    "applies_to_type": c_gy_applies_to_type,
                    "applies_to_value_ids": c_gy_applies_to_ids,
                    "excludedProductIds": c.excluded_product_ids,
                }
                c_gy_affected_ids = await self._get_affected_product_ids(c_dummy_gy)
                c_affected_ids = c_affected_ids.union(c_gy_affected_ids)
            else:
                # Amount off/Shipping/Total discount logic
                # For Business segment, check if applicable_item_type (units/cases) matches
                if "wholesaler" in roles:
                    if (c.applicable_item_type or "units") != applicable_item_type:
                        continue

            intersection = new_affected_ids.intersection(c_affected_ids)

            if intersection:
                overlaps.append(
                    {
                        "couponId": str(c.id),
                        "displayId": c.code or "",
                        "overlappingProductIds": list(intersection),
                    }
                )

        if overlaps:
            total_overlapping_products = len(set().union(*[set(o["overlappingProductIds"]) for o in overlaps]))
            return CouponValidationResponse(valid=True, totalOverlappingProducts=total_overlapping_products, details=overlaps)
        return None

    async def get_active_coupons(self) -> List[Any]:
        """Get all active coupons with a short 60s cache"""
        now = datetime.now(timezone.utc)

        if (
            self._active_coupons_cache is not None
            and self._active_coupons_cache_time
            and (now - self._active_coupons_cache_time).total_seconds() < 60
        ):
            return self._active_coupons_cache

        active_coupons = await self.storage.findAll({"is_active": True})
        self._active_coupons_cache = active_coupons
        self._active_coupons_cache_time = now
        return active_coupons

    async def get_active_automatic_product_discounts(self) -> List[Any]:
        """Get all active automatic product discounts with short caching"""
        now = datetime.now(timezone.utc)
        if (
            self._active_automatic_discounts_cache is not None
            and self._active_automatic_discounts_cache_time
            and (now - self._active_automatic_discounts_cache_time).total_seconds() < 300
        ):
            return self._active_automatic_discounts_cache

        discounts = await self.storage.findAll(
            {"method": "automatic", "is_active": True, "type_of_discount": "product_discount"}
        )

        valid_discounts = []
        for c in discounts:
            try:
                valid_from_str = c.start_date or c.start_date
                valid_until_str = c.end_date or c.end_date
                if not valid_from_str or not valid_until_str:
                    continue
                valid_from = valid_from_str if isinstance(valid_from_str, datetime) else datetime.fromisoformat(valid_from_str.replace('Z', '+00:00'))
                valid_until = valid_until_str if isinstance(valid_until_str, datetime) else datetime.fromisoformat(valid_until_str.replace('Z', '+00:00'))
                
                # Make sure both are either aware or naive
                if valid_from.tzinfo is None:
                    valid_from = valid_from.replace(tzinfo=timezone.utc)
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                    
                if valid_from <= now <= valid_until:
                    c._affected_product_ids = await self._get_affected_product_ids(c)
                    valid_discounts.append(c)
            except Exception as e:
                import traceback; traceback.print_exc()
                continue

        self._active_automatic_discounts_cache = valid_discounts
        self._active_automatic_discounts_cache_time = now
        return valid_discounts

    async def get_applicable_automatic_product_discounts(self, role: str, user_id: Optional[str] = None) -> List[Any]:
        discounts = await self.get_active_automatic_product_discounts()
        applicable = []
        for c in discounts:
            if role not in (c.applicable_roles if c.applicable_roles is not None else []):
                continue
            applicable_user_ids = c.applicable_user_ids or []
            if applicable_user_ids:
                if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                    continue
            behavior = c.user_behavior
            if behavior and behavior != "none":
                if not user_id or not await self._user_matches_behavior(user_id, behavior):
                    continue
            applicable.append(c)
        return applicable

    async def get_applicable_discounts_for_product(
        self,
        product: Any,
        role: str,
        user_id: Optional[str] = None,
        all_coupons: Optional[List[Dict]] = None,
        user_behavior_cache: Optional[Dict] = None,
    ) -> List[Any]:
        """Find other active discounts applicable to this product, excluding the default highest automatic product discount"""
        if all_coupons is None:
            all_coupons = await self.get_active_coupons()

        now = datetime.now(timezone.utc)
        default_auto_discount = None
        highest_pct = -1.0

        # Step 1: Find the default highest automatic product discount
        for c in all_coupons:
            try:
                valid_from = c.start_date if isinstance(c.start_date, datetime) else datetime.fromisoformat(c.start_date.replace('Z', '+00:00'))
                if valid_from.tzinfo is None: valid_from = valid_from.replace(tzinfo=timezone.utc)
                valid_until = c.end_date if isinstance(c.end_date, datetime) else datetime.fromisoformat(c.end_date.replace('Z', '+00:00'))
                if valid_until.tzinfo is None: valid_until = valid_until.replace(tzinfo=timezone.utc)
                if not (valid_from <= now <= valid_until):
                    continue
            except (ValueError, TypeError, AttributeError):
                logger.warning("Coupon %r has unparseable valid_from/valid_until; skipping.", getattr(c, 'id', '?'), exc_info=True)
                continue

            if c.method == "automatic" and c.type_of_discount == "product_discount":
                if role in (c.applicable_roles if c.applicable_roles is not None else []):
                    is_eligible = await self._product_eligible_async(
                        product, (c.applies_to_type if c.applies_to_type is not None else "all"), c.applies_to_value_ids, c.excluded_product_ids
                    )
                    if is_eligible:
                        applicable_user_ids = c.applicable_user_ids or []
                        if applicable_user_ids and (
                            not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]
                        ):
                            continue
                        behavior = c.user_behavior
                        if (
                            behavior
                            and behavior != "none"
                            and (
                                not user_id
                                or not await self._user_matches_behavior(
                                    user_id, behavior, user_behavior_cache=user_behavior_cache
                                )
                            )
                        ):
                            continue

                        pct = 0.0
                        if c.discount_type == "percentage":
                            pct = float(c.discount_value) if c.discount_value is not None else 0.0
                        elif c.discount_type == "fixed":
                            mrp = float(product.mrp) if product.mrp is not None else 0.0
                            if mrp > 0:
                                if not mrp:
                                    raise ValueError("Cannot calculate coupon discount: MRP is zero or None")
                                pct = (float(c.discount_value) if c.discount_value is not None else 0.0) / mrp * 100
                        if pct > highest_pct:
                            highest_pct = pct
                            default_auto_discount = c

        # Step 2: Gather all other applicable coupons
        applicable = []
        for c in all_coupons:
            if default_auto_discount and str(c.id) == str((default_auto_discount["_id"] if "_id" in default_auto_discount else None)):
                continue

            try:
                valid_from = c.start_date if isinstance(c.start_date, datetime) else datetime.fromisoformat(c.start_date.replace('Z', '+00:00'))
                if valid_from.tzinfo is None: valid_from = valid_from.replace(tzinfo=timezone.utc)
                valid_until = c.end_date if isinstance(c.end_date, datetime) else datetime.fromisoformat(c.end_date.replace('Z', '+00:00'))
                if valid_until.tzinfo is None: valid_until = valid_until.replace(tzinfo=timezone.utc)
                if not (valid_from <= now <= valid_until):
                    continue
            except (ValueError, TypeError, AttributeError):
                logger.warning("Coupon %r (step-2) has unparseable valid_from/valid_until; skipping.", getattr(c, 'id', '?'), exc_info=True)
                continue

            if role not in (c.applicable_roles if c.applicable_roles is not None else []):
                continue

            applicable_user_ids = c.applicable_user_ids or []
            if applicable_user_ids and (not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]):
                continue
            behavior = c.user_behavior
            if (
                behavior
                and behavior != "none"
                and (
                    not user_id
                    or not await self._user_matches_behavior(user_id, behavior, user_behavior_cache=user_behavior_cache)
                )
            ):
                continue

            applies = True
            if c.type_of_discount in ["product_discount", "buy_x_get_y"]:
                applies = await self._product_eligible_async(
                    product, (c.applies_to_type if c.applies_to_type is not None else "all"), c.applies_to_value_ids, c.excluded_product_ids
                )

            if applies:
                applicable.append(c)

        return applicable


def get_coupon_description(c: Any) -> str:
    method_lbl = "Use code " + c.code if c.method == "discount_code" and c.code else "Automatic offer"
    type_of_disc = c.type_of_discount
    disc_type = c.discount_type
    disc_val = c.discount_value

    if type_of_disc == "product_discount":
        if c.min_requirement_type == "quantity_based" and c.quantity_tiers:
            tiers = sorted(c.quantity_tiers, key=lambda x: x["quantity"])
            item_lbl = (c.applicable_item_type if c.applicable_item_type is not None else "units")
            tier_strs = [f"Buy {t.quantity}+ {item_lbl} get {t.discount}% off" for t in tiers]
            return f"{method_lbl}: " + ", ".join(tier_strs) + " per unit."
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off on eligible items."
    elif type_of_disc == "buy_x_get_y":
        min_qty = c.min_quantity_of_eligible_items or 1
        gets_qty = c.buy_x_get_y_customer_gets_quantity or 1
        gets_type = c.buyXGetYCustomerGetsdiscount_type
        gets_val = c.buy_x_get_y_customer_gets_discount_value

        gets_desc = "Free"
        if gets_type == "percentage":
            gets_desc = f"{gets_val}% Off"
        elif gets_type == "amount_off":
            gets_desc = f"₹{gets_val} Off"

        return f"{method_lbl}: Buy {min_qty} unit(s) and get {gets_qty} unit(s) at {gets_desc}."
    elif type_of_disc == "total_order_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        min_amt = c.min_purchase_amount or 0
        min_str = f" on orders above ₹{min_amt}" if min_amt > 0 else ""
        return f"{method_lbl}: Get {val_str} off total order{min_str}."
    elif type_of_disc == "shipping_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off shipping charges."
    else:
        return f"{method_lbl} available."


coupon_repository = CouponRepository()



