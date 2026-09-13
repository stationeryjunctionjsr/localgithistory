from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class OverlapConflictError(ValueError):
    def __init__(self, overlap_data: Any):
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
            self._categories_map = {str(c.id): getattr(c, "name", "") for c in cats if "_id" in c}
            self._categories_map_time = now
        return self._categories_map.get(str(cid))

    async def _get_brand_name(self, bid: str) -> Optional[str]:
        now = datetime.now(timezone.utc)
        if self._brands_map is None or not self._brands_map_time or (now - self._brands_map_time).total_seconds() > 60:
            brands = await self._brand_storage.findAll()
            self._brands_map = {str(b.id): getattr(b, "name", "") for b in brands if "_id" in b}
            self._brands_map_time = now
        return self._brands_map.get(str(bid))

    async def _get_collection_product_ids(self, cid: str) -> Optional[List[str]]:
        now = datetime.now(timezone.utc)
        if (
            self._collections_map is None
            or not self._collections_map_time
            or (now - self._collections_map_time).total_seconds() > 60
        ):
            cols = await self._collection_storage.findAll()
            self._collections_map = {
                str(c.id): [str(pid) for pid in getattr(c, "productIds", [])] for c in cols if "_id" in c
            }
            self._collections_map_time = now
        return self._collections_map.get(str(cid))

    async def _calculate_bxgy_discount(
        self, coupon: Any, cart_items: List[Dict], product_repository, user_role: str, user_id: str
    ) -> Any:
        applicable_item_type = getattr(coupon, "applicableItemType", "units")
        x_required = int(getattr(coupon, "minQuantityOfEligibleItems")) if getattr(coupon, "minQuantityOfEligibleItems", None) is not None else None
        y_required = int(getattr(coupon, "buyXGetYCustomerGetsQuantity")) if getattr(coupon, "buyXGetYCustomerGetsQuantity", None) is not None else None

        # Batch-load all cart products upfront to avoid N+1 (one DB hit per item)
        cart_pids = [str(getattr(item, "product", None) or getattr(item, "productId", None)) for item in cart_items if getattr(item, "product", None) or getattr(item, "productId", None)]
        if cart_pids:
            products_list = await product_repository.findAll({"allowed_ids": cart_pids})
            product_map = {str(p.id): p for p in products_list if p.id}
        else:
            product_map = {}

        elements = []
        for idx, item in enumerate(cart_items):
            pid = str(getattr(item, "product", None) or getattr(item, "productId", None))
            product = product_map.get(pid)
            if not product:
                continue
            qty = int(getattr(item, "quantity")) if getattr(item, "quantity", None) is not None else 0
            if qty <= 0:
                continue
            sell_as_case = getattr(item, 'sellAsCase', False)
            qty_per_case = int(getattr(product, "quantityPerCase")) if getattr(product, "quantityPerCase", None) is not None else 1

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
                getattr(coupon, "appliesToType", "all"),
                getattr(coupon, "appliesToValueIds", ),
                getattr(coupon, "excludedProductIds", ),
            )
            is_gy_eligible = await self._product_eligible_async(
                product,
                getattr(coupon, "buyXGetYCustomerGetsAppliesToType", "all"),
                getattr(coupon, "buyXGetYCustomerGetsAppliesToValueIds", ),
                getattr(coupon, "excludedProductIds", ),
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
            return {"discount": 0.0, "itemDiscounts": {}}

        bx_allocated = bx_candidates[:x_required]
        bx_ids = {id(e) for e in bx_allocated}

        gy_candidates = [e for e in elements if e["is_gy"] and id(e) not in bx_ids]
        gy_candidates.sort(key=lambda x: x["price"], reverse=True)
        gy_allocated = gy_candidates[:y_required]
        gy_ids = {id(e) for e in gy_allocated}

        if not gy_allocated:
            return {"discount": 0.0, "itemDiscounts": {}}

        applicable_auto = await self.get_applicable_automatic_product_discounts(user_role, user_id)
        best_auto_per_product = {}
        for e in elements:
            pid = e["pid"]
            if pid not in best_auto_per_product:
                max_d = 0.0
                for c in applicable_auto:
                    if await self._product_eligible_async(
                        e["product"],
                        getattr(c, "appliesToType", "all"),
                        getattr(c, "appliesToValueIds", None),
                        getattr(c, "excludedProductIds", None),
                    ):
                        d = (
                            (e["price"] * c.discountValue) / 100
                            if c.discountType == "percentage"
                            else c.discountValue
                        )
                        if d > max_d:
                            max_d = min(d, e["price"])
                best_auto_per_product[pid] = max_d

        gy_discount_type = getattr(coupon, "buyXGetYCustomerGetsDiscountType", "percentage")
        gy_discount_value = float(getattr(coupon, "buyXGetYCustomerGetsDiscountValue")) if getattr(coupon, "buyXGetYCustomerGetsDiscountValue", None) is not None else 0.0

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
                item_discounts[e["idx"]] = item_discounts.get(e["idx"], 0.0) + d
                total_discount += d
            for e in elements:
                if id(e) not in bx_ids and id(e) not in gy_ids:
                    d = best_auto_per_product[e["pid"]]
                    if d > 0:
                        item_discounts[e["idx"]] = item_discounts.get(e["idx"], 0.0) + d
                        total_discount += d
        else:
            for e in elements:
                d = best_auto_per_product[e["pid"]]
                if d > 0:
                    item_discounts[e["idx"]] = item_discounts.get(e["idx"], 0.0) + d
                    total_discount += d

        return {"discount": total_discount, "itemDiscounts": item_discounts, "bxgyItemIndices": bxgy_item_indices}

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
        pid = str(getattr(product, "id", ""))
        if excluded_product_ids and pid in [str(x) for x in excluded_product_ids]:
            return False
        if not applies_to_value_ids:
            return applies_to_type == "all"
        if applies_to_type == "all":
            return True
        if applies_to_type == "categories":
            cat_name = (getattr(product, "category", None) or "").strip()
            if not cat_name:
                return False
            for cid in applies_to_value_ids:
                cat_name_cached = await self._get_category_name(cid)
                if cat_name_cached and cat_name_cached.strip() == cat_name:
                    return True
            return False
        if applies_to_type == "subCategories":
            sub = (getattr(product, "subCategory", None) or "").strip()
            return sub in applies_to_value_ids if sub else False
        if applies_to_type == "brands":
            brand_name = (getattr(product, "brand", None) or "").strip()
            if not brand_name:
                return False
            for bid in applies_to_value_ids:
                brand_name_cached = await self._get_brand_name(bid)
                if brand_name_cached and brand_name_cached.strip() == brand_name:
                    return True
            return False
        if applies_to_type == "collections":
            pid = str(getattr(product, "id", ""))
            if not pid:
                return False
            for cid in applies_to_value_ids:
                product_ids_cached = await self._get_collection_product_ids(cid)
                if product_ids_cached and pid in product_ids_cached:
                    return True
            return False
        if applies_to_type == "products":
            pid = str(getattr(product, "id", ""))
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
        bid = str(getattr(bundle, "id", ""))
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
        """Check if user matches discount userBehavior. For 'registered*' consider all users; for 'downloaded*' only app users."""
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
                    if segment and "userIds" in segment:
                        if str(user_id) in [str(x) for x in segment["userIds"]]:
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
                        c_at_str = o.get("createdAt")
                        if not c_at_str or not isinstance(c_at_str, str):
                            continue
                        try:
                            c_at = datetime.fromisoformat(c_at_str.replace("Z", "+00:00"))
                            if c_at.tzinfo:
                                c_at = c_at.replace(tzinfo=None)
                            if three_months_ago <= c_at <= reference_date:
                                recent_count += 1
                        except Exception:
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

    async def create(self, coupon_data: Any):
        method = getattr(coupon_data, 'method', "discount_code")
        code = getattr(coupon_data, "code", None) or ""
        if method == "discount_code" and code:
            existing = await self.findByCode(code)
            if existing:
                raise ValueError("Discount code already exists")
            code = code.upper()
        elif method == "automatic":
            code = None  # no code for automatic

        applicable_roles = getattr(coupon_data, 'applicableRoles', ["customer"])
        prefix = "DISC-WH-" if "wholesaler" in applicable_roles else "DISC-RT-"

        # In simple array/json memory we can just filter
        # But motor query logic isn't always fully deterministic here if implemented purely as find
        # Let's get all coupons and manually find max to ensure safety across DBs
        all_coupons = await self.storage.findAll({})
        max_num = 0
        for doc in all_coupons:
            did = getattr(doc, "displayId", "")
            if did.startswith(prefix):
                try:
                    num = int(did[len(prefix) :])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        display_id = f"{prefix}{max_num + 1}"

        coupon = {
            "typeOfDiscount": getattr(coupon_data, 'typeOfDiscount', "product_discount"),
            "code": code,
            "method": method,
            "discountType": getattr(coupon_data, 'discountType', "percentage"),
            "discountValue": float(coupon_data.discountValue),
            "minPurchaseAmount": float(getattr(coupon_data, 'minPurchaseAmount')),
            "minRequirementType": getattr(coupon_data, 'minRequirementType', "none"),
            "minQuantityOfEligibleItems": int(coupon_data.minQuantityOfEligibleItems)
            if getattr(coupon_data, "minQuantityOfEligibleItems", None) is not None
            else None,
            "maxDiscountAmount": float(coupon_data.maxDiscountAmount)
            if getattr(coupon_data, "maxDiscountAmount", None)
            else None,
            "validFrom": getattr(coupon_data, 'validFrom', datetime.now(timezone.utc).isoformat()),
            "validUntil": coupon_data.validUntil,
            "usageLimit": int(coupon_data.usageLimit) if getattr(coupon_data, "usageLimit", None) else None,
            "usedCount": 0,
            "isActive": getattr(coupon_data, 'isActive', True),
            "applicableRoles": getattr(coupon_data, 'applicableRoles', ["customer"]),
            "applicableUserIds": getattr(coupon_data, "applicableUserIds", None) or [],
            "applicableCategories": getattr(coupon_data, 'applicableCategories', []),
            "applicablePaymentMethods": getattr(coupon_data, 'applicablePaymentMethods', ["cod", "upi", "credit"]),
            "maxUsagePerUser": int(coupon_data.maxUsagePerUser) if getattr(coupon_data, "maxUsagePerUser", None) else None,
            "userUsages": {},
            "appliesToType": getattr(coupon_data, 'appliesToType', "all"),
            "appliesToValueIds": getattr(coupon_data, "appliesToValueIds", None) or [],
            "userBehavior": getattr(coupon_data, "userBehavior", None) or None,
            "buyXGetYCustomerGetsQuantity": int(coupon_data.buyXGetYCustomerGetsQuantity)
            if getattr(coupon_data, "buyXGetYCustomerGetsQuantity", None)
            else None,
            "buyXGetYCustomerGetsAppliesToType": getattr(coupon_data, "buyXGetYCustomerGetsAppliesToType", None),
            "buyXGetYCustomerGetsAppliesToValueIds": getattr(coupon_data, "buyXGetYCustomerGetsAppliesToValueIds", None) or [],
            "buyXGetYCustomerGetsDiscountType": getattr(coupon_data, "buyXGetYCustomerGetsDiscountType", None),
            "buyXGetYCustomerGetsDiscountValue": float(coupon_data.buyXGetYCustomerGetsDiscountValue)
            if getattr(coupon_data, "buyXGetYCustomerGetsDiscountValue", None) is not None
            else None,
            "displayId": display_id,
            "excludedProductIds": getattr(coupon_data, "excludedProductIds", None) or [],
            "applicableItemType": getattr(coupon_data, "applicableItemType", None) or "units",
            "couponMode": getattr(coupon_data, 'couponMode', "override"),
            "quantityTiers": [
                {"quantity": int(t.quantity), "discount": float(t.discount)} for t in coupon_data.quantityTiers
            ]
            if getattr(coupon_data, "quantityTiers", None) is not None
            else None,
        }

        # Handle Overlap
        resolution = getattr(coupon_data, "resolution", None)
        force = getattr(coupon_data, 'force', False)

        if not force:
            overlap = await self.check_discount_overlap(coupon)
            if overlap:
                if resolution == "overwrite":
                    # Add exclusions to existing coupons
                    for detail in overlap["details"]:
                        existing_coupon = await self.findById(detail["couponId"])
                        if existing_coupon:
                            excl = set(existing_getattr(coupon, "excludedProductIds", ) or [])
                            excl.update(detail["overlappingProductIds"])
                            await self.storage.update(detail["couponId"], {"excludedProductIds": list(excl)})
                elif resolution == "retain":
                    # Add exclusions to current coupon
                    excl = set(getattr(coupon, "excludedProductIds", ) or [])
                    pids_to_exclude = set().union(*[set(d.overlappingProductIds) for d in overlap["details"]])

                    # Check if all targeted products are excluded/covered
                    targeted_pids = await self._get_affected_product_ids(coupon)
                    if targeted_pids.issubset(pids_to_exclude):
                        raise ValueError(
                            "Discount not created because all targeted products are covered by retained earlier discounts"
                        )

                    excl.update(list(pids_to_exclude))
                    coupon.excludedProductIds = list(excl)
                else:
                    raise OverlapConflictError(overlap)

        res = await self.storage.create(coupon)
        self.invalidate_cache()
        return res

    async def update(self, id: str, update_data: Any):
        if "code" in update_data and getattr(update_data, "code", None):
            existing = await self.findByCode(update_data.code)
            if existing and existing.id != id:
                raise ValueError("Discount code already in use")
            update_data.code = update_data.code.upper()
        if getattr(update_data, "method", None) == "automatic":
            update_data.code = None
        if "discountValue" in update_data:
            update_data.discountValue = float(update_data.discountValue)
        if "minPurchaseAmount" in update_data:
            update_data.minPurchaseAmount = float(update_data.minPurchaseAmount)
        if "minQuantityOfEligibleItems" in update_data and update_data.minQuantityOfEligibleItems is not None:
            update_data.minQuantityOfEligibleItems = int(update_data.minQuantityOfEligibleItems)
        if "maxDiscountAmount" in update_data and update_data.maxDiscountAmount:
            update_data.maxDiscountAmount = float(update_data.maxDiscountAmount)
        if "usageLimit" in update_data and update_data.usageLimit:
            update_data.usageLimit = int(update_data.usageLimit)
        if "maxUsagePerUser" in update_data and update_data.maxUsagePerUser:
            update_data.maxUsagePerUser = int(update_data.maxUsagePerUser)
        if "appliesToValueIds" in update_data and update_data.appliesToValueIds is None:
            update_data.appliesToValueIds = []
        if "applicableUserIds" in update_data and update_data.applicableUserIds is None:
            update_data.applicableUserIds = []
        if "buyXGetYCustomerGetsQuantity" in update_data and update_data.buyXGetYCustomerGetsQuantity is not None:
            update_data.buyXGetYCustomerGetsQuantity = int(update_data.buyXGetYCustomerGetsQuantity)
        if (
            "buyXGetYCustomerGetsDiscountValue" in update_data
            and update_data.buyXGetYCustomerGetsDiscountValue is not None
        ):
            update_data.buyXGetYCustomerGetsDiscountValue = float(update_data.buyXGetYCustomerGetsDiscountValue)
        if (
            "buyXGetYCustomerGetsAppliesToValueIds" in update_data
            and update_data.buyXGetYCustomerGetsAppliesToValueIds is None
        ):
            update_data.buyXGetYCustomerGetsAppliesToValueIds = []
        if "quantityTiers" in update_data and update_data.quantityTiers is not None:
            update_data.quantityTiers = [
                {"quantity": int(getattr(t, "quantity", None)), "discount": float(getattr(t, "discount", None))}
                for t in update_data.quantityTiers
            ]

        # Handle Overlap
        resolution = getattr(update_data, "resolution", None)
        force = getattr(update_data, 'force', False)

        if not force:
            # We need the full data for overlap check
            existing = await self.findById(id)
            if not existing:
                return None
            full_data = {**existing, **update_data}
            overlap = await self.check_discount_overlap(full_data, exclude_coupon_id=id)
            if overlap:
                if resolution == "overwrite":
                    for detail in overlap["details"]:
                        conflicting = await self.findById(detail["couponId"])
                        if conflicting:
                            excl = set(conflicting.get("excludedProductIds") or [])
                            excl.update(detail["overlappingProductIds"])
                            await self.storage.update(detail["couponId"], {"excludedProductIds": list(excl)})
                elif resolution == "retain":
                    excl = set(getattr(update_data, "excludedProductIds", None) or getattr(existing, "excludedProductIds", None) or [])
                    pids_to_exclude = set().union(*[set(d.overlappingProductIds) for d in overlap["details"]])

                    # Check if all targeted products are excluded/covered
                    targeted_pids = await self._get_affected_product_ids(full_data)
                    if targeted_pids.issubset(pids_to_exclude):
                        raise ValueError(
                            "Discount not updated because all targeted products are covered by retained earlier discounts"
                        )

                    excl.update(list(pids_to_exclude))
                    update_data.excludedProductIds = list(excl)
                else:
                    raise OverlapConflictError(overlap)

        res = await self.storage.update(id, update_data)
        self.invalidate_cache()
        return res

    async def delete(self, id: str):
        res = await self.storage.delete(id)
        self.invalidate_cache()
        return res

    async def incrementUsage(self, id: str, user_id: str):
        coupon = await self.findById(id)
        if not coupon:
            return None

        user_usages = getattr(coupon, "userUsages", {})
        user_usages[user_id] = user_usages.get(user_id, 0) + 1

        return await self.update(id, {"usedCount": (getattr(coupon, "usedCount") if getattr(coupon, "usedCount", None) is not None else 0) + 1, "userUsages": user_usages})

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
            return {"valid": False, "message": "Invalid coupon code"}

        if not getattr(coupon, "isActive", True):
            return {"valid": False, "message": "Discount is not active"}

        now = datetime.now(timezone.utc)
        valid_from = datetime.fromisoformat(getattr(coupon, "validFrom").replace("Z", "+00:00"))
        valid_until = datetime.fromisoformat(getattr(coupon, "validUntil").replace("Z", "+00:00"))

        if now < valid_from:
            return {"valid": False, "message": "Discount is not yet valid"}

        if now > valid_until:
            return {"valid": False, "message": "Discount has expired"}

        if getattr(coupon, "usageLimit", ) and getattr(coupon, "usedCount", 0) >= getattr(coupon, "usageLimit"):
            return {"valid": False, "message": "Discount usage limit reached"}

        if getattr(coupon, "maxUsagePerUser", ):
            user_usages = getattr(coupon, "userUsages", {})
            if user_usages.get(user_id, 0) >= getattr(coupon, "maxUsagePerUser"):
                return {
                    "valid": False,
                    "message": f"You have reached the maximum usage limit ({coupon['maxUsagePerUser']}) for this discount",
                }

        if user_role not in getattr(coupon, "applicableRoles", []):
            return {"valid": False, "message": "Discount not applicable for your role"}

        # Selective customers & User behavior segments check
        applicable_user_ids = getattr(coupon, "applicableUserIds", ) or []
        user_behavior = getattr(coupon, "userBehavior", )
        has_specific_users = len(applicable_user_ids) > 0 or (user_behavior and user_behavior != "none")

        if has_specific_users:
            matches_selective = str(user_id) in [str(x) for x in applicable_user_ids]
            matches_behavior = (
                await self._user_matches_behavior(user_id, user_behavior)
                if (user_behavior and user_behavior != "none")
                else False
            )
            if not (matches_selective or matches_behavior):
                return {"valid": False, "message": "Discount not applicable for your account"}

        applicable_payment_methods = getattr(coupon, "applicablePaymentMethods", )
        if (
            applicable_payment_methods is not None
            and payment_method
            and payment_method.lower() not in [m.lower() for m in applicable_payment_methods]
        ):
            return {"valid": False, "message": f"Discount not applicable for {payment_method.upper()} payment method"}

        if getattr(coupon, "typeOfDiscount", ) == "shipping_discount":
            if not shipping_address:
                # Try to get from user
                from app.repositories.user_repository import user_repository

                user_record = await user_repository.findById(user_id)
                if user_record and user_record.get("address"):
                    shipping_address = user_record.get("address")

            if shipping_address:
                pincode = shipping_address.get("zipCode") or shipping_address.get("pincode")
                if not pincode:
                    return {"valid": False, "message": "Shipping address must include a pincode for this discount."}
                allowed_pincodes = getattr(coupon, "shippingPincodes", ) or []
                if allowed_pincodes and str(pincode).strip() not in [str(p).strip() for p in allowed_pincodes]:
                    return {
                        "valid": False,
                        "message": f"This shipping discount is not applicable for pincode {pincode}.",
                    }
            else:
                return {"valid": False, "message": "A shipping address is required to apply this shipping discount."}

        # Resolve purchase amount and eligible quantity from cart items (eligible only) or from argument
        purchase_amount_to_use = purchase_amount
        eligible_item_indices = None
        eligible_quantity = 0
        if cart_items and product_repository:
            eligible_item_indices = []
            applies_to_type = getattr(coupon, "appliesToType", ) or "all"
            applies_to_ids = getattr(coupon, "appliesToValueIds", ) or []
            eligible_subtotal = 0.0
            for idx, item in enumerate(cart_items):
                product = await product_repository.findById(getattr(item, "product", None) or getattr(item, "productId", None))
                if not product:
                    continue
                if await self._product_eligible_async(
                    product,
                    applies_to_type,
                    applies_to_ids if applies_to_ids else None,
                    getattr(coupon, "excludedProductIds", ),
                ):
                    qty = getattr(item, 'quantity', 0)
                    eligible_quantity += qty
                    sell_as_case = getattr(item, 'sellAsCase', False)
                    ignore_auto = getattr(coupon, "method", ) == "discount_code" and getattr(coupon, "couponMode", ) == "override"
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
            applicable_categories = getattr(coupon, "applicableCategories", [])
            if applicable_categories and category and category not in applicable_categories:
                return {"valid": False, "message": "Discount not applicable for this category"}

        min_req = getattr(coupon, "minRequirementType", ) or "none"
        if min_req == "min_amount" and purchase_amount_to_use < getattr(coupon, "minPurchaseAmount", 0):
            return {
                "valid": False,
                "message": f"Minimum purchase amount of {coupon['minPurchaseAmount']} required (on eligible items)",
            }
        if min_req == "min_quantity":
            min_qty = getattr(coupon, "minQuantityOfEligibleItems", ) or 0
            if eligible_quantity < min_qty:
                return {
                    "valid": False,
                    "message": f"Minimum quantity of {min_qty} eligible items required (you have {eligible_quantity} eligible in cart)",
                }
            if not cart_items and min_qty > 0:
                return {
                    "valid": False,
                    "message": "Minimum quantity requirement cannot be validated without cart items",
                }

        # Calculate discount on eligible amount only
        discount = 0.0
        item_discounts = None
        bxgy_item_indices = None
        if getattr(coupon, "typeOfDiscount", ) == "buy_x_get_y" and cart_items and product_repository:
            bxgy_res = await self._calculate_bxgy_discount(coupon, cart_items, product_repository, user_role, user_id)
            discount = bxgy_res["discount"]
            item_discounts = bxgy_res["itemDiscounts"]
            bxgy_item_indices = bxgy_res.get("bxgyItemIndices")
        elif getattr(coupon, "typeOfDiscount", ) == "shipping_discount":
            if getattr(coupon, "discountType") == "percentage":
                discount = (shipping_charge * getattr(coupon, "discountValue")) / 100
                if getattr(coupon, "maxDiscountAmount", ):
                    discount = min(discount, getattr(coupon, "maxDiscountAmount"))
            else:
                discount = getattr(coupon, "discountValue")
            discount = min(discount, shipping_charge)
        else:
            if getattr(coupon, "discountType") == "percentage":
                discount = (purchase_amount_to_use * getattr(coupon, "discountValue")) / 100
                if getattr(coupon, "maxDiscountAmount", ):
                    discount = min(discount, getattr(coupon, "maxDiscountAmount"))
            else:
                if getattr(coupon, "typeOfDiscount", ) == "product_discount":
                    discount = eligible_quantity * getattr(coupon, "discountValue")
                else:
                    discount = getattr(coupon, "discountValue")

        out = {"valid": True, "coupon": coupon, "discount": round(discount, 2)}
        if eligible_item_indices is not None:
            out["eligibleItemIndices"] = eligible_item_indices
        if item_discounts is not None:
            out["itemDiscounts"] = item_discounts
        if bxgy_item_indices is not None:
            out["bxgyItemIndices"] = bxgy_item_indices
        return out

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
        all_coupons = await self.storage.findAll({"method": "automatic", "isActive": True})
        results = []
        for coupon in all_coupons:
            try:
                if getattr(coupon, "typeOfDiscount", ) == "product_discount":
                    continue
                valid_from = datetime.fromisoformat(getattr(coupon, "validFrom").replace("Z", "+00:00"))
                valid_until = datetime.fromisoformat(getattr(coupon, "validUntil").replace("Z", "+00:00"))
                if now < valid_from or now > valid_until:
                    continue
                if getattr(coupon, "usageLimit") and (getattr(coupon, "usedCount") if getattr(coupon, "usedCount", None) is not None else 0) >= getattr(coupon, "usageLimit"):
                    continue
                if user_role not in getattr(coupon, "applicableRoles", []):
                    continue
                applicable_user_ids = getattr(coupon, "applicableUserIds", ) or []
                user_behavior = getattr(coupon, "userBehavior", )
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
                    applicable_payment_methods = getattr(coupon, "applicablePaymentMethods", )
                    if applicable_payment_methods is not None and payment_method.lower() not in [
                        m.lower() for m in applicable_payment_methods
                    ]:
                        continue

                if getattr(coupon, "typeOfDiscount", ) == "shipping_discount":
                    addr = shipping_address
                    if not addr:
                        from app.repositories.user_repository import user_repository

                        u = await user_repository.findById(user_id)
                        if u and getattr(u, "address", None):
                            addr = getattr(u, "address", None)

                    if addr:
                        pincode = addr.get("zipCode") or addr.get("pincode")
                        if not pincode:
                            continue
                        allowed_pincodes = getattr(coupon, "shippingPincodes", ) or []
                        if allowed_pincodes and str(pincode).strip() not in [str(p).strip() for p in allowed_pincodes]:
                            continue
                    else:
                        continue
                # Compute eligible subtotal and quantity
                applies_to_type = getattr(coupon, "appliesToType", ) or "all"
                applies_to_ids = getattr(coupon, "appliesToValueIds", ) or []
                eligible_subtotal = 0.0
                eligible_quantity = 0
                eligible_item_indices = []
                for idx, item in enumerate(cart_items):
                    product = await product_repository.findById(getattr(item, "product", None) or getattr(item, "productId", None))
                    if not product:
                        continue
                    if await self._product_eligible_async(
                        product,
                        applies_to_type,
                        applies_to_ids if applies_to_ids else None,
                        getattr(coupon, "excludedProductIds", ),
                    ):
                        qty = getattr(item, 'quantity', 0)
                        eligible_quantity += qty
                        sell_as_case = getattr(item, 'sellAsCase', False)
                        item_total = product_repository.calculateTotalPrice(
                            product, user_role, qty, sell_as_case=sell_as_case, user_id=user_id
                        )
                        eligible_subtotal += item_total
                        eligible_item_indices.append(idx)
                min_req = getattr(coupon, "minRequirementType", ) or "none"
                if min_req == "min_amount" and eligible_subtotal < getattr(coupon, "minPurchaseAmount", 0):
                    continue
                if min_req == "min_quantity":
                    min_qty = int(getattr(coupon, "minQuantityOfEligibleItems")) if getattr(coupon, "minQuantityOfEligibleItems", None) is not None else 0
                    if eligible_quantity < min_qty:
                        continue
                if getattr(coupon, "maxUsagePerUser", ):
                    user_usages = getattr(coupon, "userUsages", {})
                    if user_usages.get(user_id, 0) >= getattr(coupon, "maxUsagePerUser"):
                        continue
                discount = 0.0
                item_discounts = None
                bxgy_item_indices = None
                if getattr(coupon, "typeOfDiscount", ) == "buy_x_get_y":
                    bxgy_res = await self._calculate_bxgy_discount(
                        coupon, cart_items, product_repository, user_role, user_id
                    )
                    discount = bxgy_res["discount"]
                    item_discounts = bxgy_res["itemDiscounts"]
                    bxgy_item_indices = bxgy_res.get("bxgyItemIndices")
                elif getattr(coupon, "typeOfDiscount", ) == "shipping_discount":
                    if getattr(coupon, "discountType") == "percentage":
                        discount = (shipping_charge * getattr(coupon, "discountValue")) / 100
                        if getattr(coupon, "maxDiscountAmount", ):
                            discount = min(discount, getattr(coupon, "maxDiscountAmount"))
                    else:
                        discount = getattr(coupon, "discountValue")
                    discount = min(discount, shipping_charge)
                else:
                    if getattr(coupon, "discountType") == "percentage":
                        discount = (eligible_subtotal * getattr(coupon, "discountValue")) / 100
                        if getattr(coupon, "maxDiscountAmount", ):
                            discount = min(discount, getattr(coupon, "maxDiscountAmount"))
                    else:
                        if getattr(coupon, "typeOfDiscount", ) == "product_discount":
                            discount = eligible_quantity * getattr(coupon, "discountValue")
                        else:
                            discount = getattr(coupon, "discountValue")
                results.append(
                    {
                        "coupon": coupon,
                        "discount": round(discount, 2),
                        "eligibleItemIndices": eligible_item_indices,
                        "itemDiscounts": item_discounts,
                        "bxgyItemIndices": bxgy_item_indices,
                    }
                )
            except Exception:
                continue
        return results

    async def _get_affected_product_ids(self, coupon_data: Any) -> set:
        """Expand appliesToType/ValueIds into a set of product IDs."""
        applies_to_type = getattr(coupon_data, "appliesToType", None) or "all"
        applies_to_value_ids = getattr(coupon_data, "appliesToValueIds", None) or []
        excluded_product_ids = set(str(x) for x in (getattr(coupon_data, "excludedProductIds", None) or []))

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
                    pids = col.get("productIds") or []
                    for pid in pids:
                        eligible_collection_product_ids.add(str(pid))
            return set(pid for pid in eligible_collection_product_ids if pid not in excluded_product_ids)

        # Build query filters to load only matching products from database
        query = {"isActive": True}
        eligible_category_names = set()
        eligible_brand_names = set()

        if applies_to_type == "categories" and applies_to_value_ids:
            for cid in applies_to_value_ids:
                cat = await self._category_storage.findById(cid)
                if cat and cat.get("name"):
                    eligible_category_names.add(cat.get("name").strip())
            if eligible_category_names:
                query["categories"] = ",".join(eligible_category_names)
            else:
                return set()
        elif applies_to_type == "brands" and applies_to_value_ids:
            for bid in applies_to_value_ids:
                brand = await self._brand_storage.findById(bid)
                if brand and getattr(brand, "name", None):
                    eligible_brand_names.add(getattr(brand, "name", None).strip())
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
            pid = str(getattr(p, "id", ""))
            if pid in excluded_product_ids:
                continue

            if applies_to_type == "all":
                affected.add(pid)
            elif applies_to_type == "categories":
                p_cat = (getattr(p, "category", None) or "").strip().lower()
                if p_cat and p_cat in {c.lower() for c in eligible_category_names}:
                    affected.add(pid)
            elif applies_to_type == "subCategories":
                p_sub = (getattr(p, "subCategory", None) or "").strip()
                if p_sub and p_sub in applies_to_value_ids:
                    affected.add(pid)
            elif applies_to_type == "brands":
                p_brand = (getattr(p, "brand", None) or "").strip().lower()
                if p_brand and p_brand in {b.lower() for b in eligible_brand_names}:
                    affected.add(pid)

        return affected

    async def check_discount_overlap(self, coupon_data: Any, exclude_coupon_id: Optional[str] = None):
        """Identify conflicting active coupons and return affected product count."""
        if not getattr(coupon_data, 'isActive', True):
            return None

        roles = getattr(coupon_data, "applicableRoles", None) or []
        all_coupons = await self.storage.findAll({"isActive": True})

        # Filter for same roles
        conflicting_candidates = [
            c
            for c in all_coupons
            if any(r in (getattr(c, "applicableRoles", None) or []) for r in roles) and str(c.id) != str(exclude_coupon_id)
        ]

        new_affected_ids = await self._get_affected_product_ids(coupon_data)
        type_of_discount = getattr(coupon_data, "typeOfDiscount", None) or "product_discount"

        if type_of_discount == "buy_x_get_y":
            gy_applies_to_type = getattr(coupon_data, 'buyXGetYCustomerGetsAppliesToType', "all")
            gy_applies_to_ids = getattr(coupon_data, "buyXGetYCustomerGetsAppliesToValueIds", None) or []
            dummy_gy_coupon = {
                "appliesToType": gy_applies_to_type,
                "appliesToValueIds": gy_applies_to_ids,
                "excludedProductIds": getattr(coupon_data, "excludedProductIds", None),
            }
            gy_affected_ids = await self._get_affected_product_ids(dummy_gy_coupon)
            new_affected_ids = new_affected_ids.union(gy_affected_ids)

        if not new_affected_ids:
            return None

        applicable_item_type = getattr(coupon_data, "applicableItemType", None) or "units"

        overlaps = []
        for c in conflicting_candidates:
            c_type = getattr(c, "typeOfDiscount", None) or "product_discount"
            if c_type != type_of_discount:
                continue

            is_bxgy = type_of_discount == "buy_x_get_y"
            c_affected_ids = await self._get_affected_product_ids(c)
            if is_bxgy:
                c_gy_applies_to_type = getattr(c, "buyXGetYCustomerGetsAppliesToType", "all")
                c_gy_applies_to_ids = getattr(c, "buyXGetYCustomerGetsAppliesToValueIds", None) or []
                c_dummy_gy = {
                    "appliesToType": c_gy_applies_to_type,
                    "appliesToValueIds": c_gy_applies_to_ids,
                    "excludedProductIds": getattr(c, "excludedProductIds", None),
                }
                c_gy_affected_ids = await self._get_affected_product_ids(c_dummy_gy)
                c_affected_ids = c_affected_ids.union(c_gy_affected_ids)
            else:
                # Amount off/Shipping/Total discount logic
                # For Business segment, check if applicableItemType (units/cases) matches
                if "wholesaler" in roles:
                    if (getattr(c, "applicableItemType", None) or "units") != applicable_item_type:
                        continue

            intersection = new_affected_ids.intersection(c_affected_ids)

            if intersection:
                overlaps.append(
                    {
                        "couponId": str(c.id),
                        "displayId": getattr(c, "displayId", None),
                        "overlappingProductIds": list(intersection),
                    }
                )

        if overlaps:
            total_overlapping_products = len(set().union(*[set(o["overlappingProductIds"]) for o in overlaps]))
            return {"totalOverlappingProducts": total_overlapping_products, "details": overlaps}
        return None

    async def get_active_coupons(self) -> List[Any]:
        """Get all active coupons with a short 60s cache"""
        now = datetime.now(timezone.utc)
        if not hasattr(self, "_active_coupons_cache"):
            self._active_coupons_cache = None
            self._active_coupons_cache_time = None

        if (
            self._active_coupons_cache is not None
            and self._active_coupons_cache_time
            and (now - self._active_coupons_cache_time).total_seconds() < 60
        ):
            return self._active_coupons_cache

        active_coupons = await self.storage.findAll({"isActive": True})
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
            {"method": "automatic", "isActive": True, "typeOfDiscount": "product_discount"}
        )

        valid_discounts = []
        for c in discounts:
            try:
                valid_from_str = getattr(c, "validFrom", None) or getattr(c, "startDate", None)
                valid_until_str = getattr(c, "validUntil", None) or getattr(c, "endDate", None)
                if not valid_from_str or not valid_until_str:
                    continue
                valid_from = datetime.fromisoformat(valid_from_str.replace("Z", "+00:00"))
                valid_until = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
                
                # Make sure both are either aware or naive
                if valid_from.tzinfo is None:
                    valid_from = valid_from.replace(tzinfo=timezone.utc)
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                    
                if valid_from <= now <= valid_until:
                    c._affected_product_ids = await self._get_affected_product_ids(c)
                    valid_discounts.append(c)
            except Exception as e:
                print("Exception in coupon check:", e)
                continue

        self._active_automatic_discounts_cache = valid_discounts
        self._active_automatic_discounts_cache_time = now
        return valid_discounts

    async def get_applicable_automatic_product_discounts(self, role: str, user_id: Optional[str] = None) -> List[Any]:
        discounts = await self.get_active_automatic_product_discounts()
        applicable = []
        for c in discounts:
            if role not in getattr(c, "applicableRoles", []):
                continue
            applicable_user_ids = getattr(c, "applicableUserIds", None) or []
            if applicable_user_ids:
                if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                    continue
            behavior = getattr(c, "userBehavior", None)
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
                valid_from = datetime.fromisoformat(c.validFrom.replace("Z", "+00:00")).replace(tzinfo=None)
                valid_until = datetime.fromisoformat(c.validUntil.replace("Z", "+00:00")).replace(tzinfo=None)
                if not (valid_from <= now <= valid_until):
                    continue
            except Exception:
                continue

            if getattr(c, "method", None) == "automatic" and getattr(c, "typeOfDiscount", None) == "product_discount":
                if role in getattr(c, "applicableRoles", []):
                    is_eligible = await self._product_eligible_async(
                        product, getattr(c, "appliesToType", "all"), getattr(c, "appliesToValueIds", None), getattr(c, "excludedProductIds", None)
                    )
                    if is_eligible:
                        applicable_user_ids = getattr(c, "applicableUserIds", None) or []
                        if applicable_user_ids and (
                            not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]
                        ):
                            continue
                        behavior = getattr(c, "userBehavior", None)
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
                        if getattr(c, "discountType", None) == "percentage":
                            pct = float(getattr(c, "discountValue")) if getattr(c, "discountValue", None) is not None else 0.0
                        elif getattr(c, "discountType", None) == "fixed":
                            mrp = float(getattr(product, "mrp")) if getattr(product, "mrp", None) is not None else 0.0
                            if mrp > 0:
                                pct = (float(getattr(c, "discountValue")) if getattr(c, "discountValue", None) is not None else 0.0) / mrp * 100
                        if pct > highest_pct:
                            highest_pct = pct
                            default_auto_discount = c

        # Step 2: Gather all other applicable coupons
        applicable = []
        for c in all_coupons:
            if default_auto_discount and str(c.id) == str(default_auto_discount.get("_id")):
                continue

            try:
                valid_from = datetime.fromisoformat(c.validFrom.replace("Z", "+00:00")).replace(tzinfo=None)
                valid_until = datetime.fromisoformat(c.validUntil.replace("Z", "+00:00")).replace(tzinfo=None)
                if not (valid_from <= now <= valid_until):
                    continue
            except Exception:
                continue

            if role not in getattr(c, "applicableRoles", []):
                continue

            applicable_user_ids = getattr(c, "applicableUserIds", None) or []
            if applicable_user_ids and (not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]):
                continue
            behavior = getattr(c, "userBehavior", None)
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
            if getattr(c, "typeOfDiscount", None) in ["product_discount", "buy_x_get_y"]:
                applies = await self._product_eligible_async(
                    product, getattr(c, "appliesToType", "all"), getattr(c, "appliesToValueIds", None), getattr(c, "excludedProductIds", None)
                )

            if applies:
                applicable.append(c)

        return applicable


def get_coupon_description(c: Any) -> str:
    method_lbl = "Use code " + c.code if getattr(c, "method", None) == "discount_code" and getattr(c, "code", None) else "Automatic offer"
    type_of_disc = getattr(c, "typeOfDiscount", None)
    disc_type = getattr(c, "discountType", None)
    disc_val = getattr(c, "discountValue", None)

    if type_of_disc == "product_discount":
        if getattr(c, "minRequirementType", None) == "quantity_based" and getattr(c, "quantityTiers", None):
            tiers = sorted(c.quantityTiers, key=lambda x: x["quantity"])
            item_lbl = getattr(c, "applicableItemType", "units")
            tier_strs = [f"Buy {t.quantity}+ {item_lbl} get {t.discount}% off" for t in tiers]
            return f"{method_lbl}: " + ", ".join(tier_strs) + " per unit."
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off on eligible items."
    elif type_of_disc == "buy_x_get_y":
        min_qty = getattr(c, "minQuantityOfEligibleItems", None) or 1
        gets_qty = getattr(c, "buyXGetYCustomerGetsQuantity", None) or 1
        gets_type = getattr(c, "buyXGetYCustomerGetsDiscountType", None)
        gets_val = getattr(c, "buyXGetYCustomerGetsDiscountValue", None)

        gets_desc = "Free"
        if gets_type == "percentage":
            gets_desc = f"{gets_val}% Off"
        elif gets_type == "amount_off":
            gets_desc = f"₹{gets_val} Off"

        return f"{method_lbl}: Buy {min_qty} unit(s) and get {gets_qty} unit(s) at {gets_desc}."
    elif type_of_disc == "total_order_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        min_amt = getattr(c, "minPurchaseAmount", None) or 0
        min_str = f" on orders above ₹{min_amt}" if min_amt > 0 else ""
        return f"{method_lbl}: Get {val_str} off total order{min_str}."
    elif type_of_disc == "shipping_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off shipping charges."
    else:
        return f"{method_lbl} available."


coupon_repository = CouponRepository()



