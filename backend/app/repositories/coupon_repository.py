from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class OverlapConflictError(ValueError):
    def __init__(self, overlap_data: Dict):
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
        now = datetime.utcnow()
        if (
            self._categories_map is None
            or not self._categories_map_time
            or (now - self._categories_map_time).total_seconds() > 60
        ):
            cats = await self._category_storage.findAll()
            self._categories_map = {str(c["_id"]): c.get("name", "") for c in cats if "_id" in c}
            self._categories_map_time = now
        return self._categories_map.get(str(cid))

    async def _get_brand_name(self, bid: str) -> Optional[str]:
        now = datetime.utcnow()
        if (
            self._brands_map is None
            or not self._brands_map_time
            or (now - self._brands_map_time).total_seconds() > 60
        ):
            brands = await self._brand_storage.findAll()
            self._brands_map = {str(b["_id"]): b.get("name", "") for b in brands if "_id" in b}
            self._brands_map_time = now
        return self._brands_map.get(str(bid))

    async def _get_collection_product_ids(self, cid: str) -> Optional[List[str]]:
        now = datetime.utcnow()
        if (
            self._collections_map is None
            or not self._collections_map_time
            or (now - self._collections_map_time).total_seconds() > 60
        ):
            cols = await self._collection_storage.findAll()
            self._collections_map = {str(c["_id"]): [str(pid) for pid in c.get("productIds", [])] for c in cols if "_id" in c}
            self._collections_map_time = now
        return self._collections_map.get(str(cid))

    async def _calculate_bxgy_discount(self, coupon: Dict, cart_items: List[Dict], product_repository, user_role: str, user_id: str) -> Dict:
        applicable_item_type = coupon.get("applicableItemType", "units")
        x_required = int(coupon.get("minQuantityOfEligibleItems") or 0)
        y_required = int(coupon.get("buyXGetYCustomerGetsQuantity") or 0)
        
        elements = []
        for idx, item in enumerate(cart_items):
            pid = str(item.get("product") or item.get("productId"))
            product = await product_repository.findById(pid)
            if not product:
                continue
            qty = int(item.get("quantity") or 0)
            if qty <= 0:
                continue
            sell_as_case = item.get("sellAsCase", False)
            qty_per_case = int(product.get("quantityPerCase") or 1)
            
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
                product, coupon.get("appliesToType", "all"), coupon.get("appliesToValueIds"), coupon.get("excludedProductIds")
            )
            is_gy_eligible = await self._product_eligible_async(
                product, coupon.get("buyXGetYCustomerGetsAppliesToType", "all"), coupon.get("buyXGetYCustomerGetsAppliesToValueIds"), coupon.get("excludedProductIds")
            )
            for _ in range(element_qty):
                elements.append({
                    "idx": idx,
                    "pid": pid,
                    "price": element_price,
                    "is_bx": is_bx_eligible,
                    "is_gy": is_gy_eligible,
                    "product": product,
                })
                
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
                    if await self._product_eligible_async(e["product"], c.get("appliesToType", "all"), c.get("appliesToValueIds"), c.get("excludedProductIds")):
                        d = (e["price"] * c["discountValue"]) / 100 if c["discountType"] == "percentage" else c["discountValue"]
                        if d > max_d:
                            max_d = min(d, e["price"])
                best_auto_per_product[pid] = max_d
                
        gy_discount_type = coupon.get("buyXGetYCustomerGetsDiscountType", "percentage")
        gy_discount_value = float(coupon.get("buyXGetYCustomerGetsDiscountValue") or 0)
        
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
        product: Dict,
        applies_to_type: str,
        applies_to_value_ids: Optional[List[str]],
        excluded_product_ids: Optional[List[str]] = None,
    ) -> bool:
        pid = str(product.get("_id", ""))
        if excluded_product_ids and pid in [str(x) for x in excluded_product_ids]:
            return False
        if not applies_to_value_ids:
            return applies_to_type == "all"
        if applies_to_type == "all":
            return True
        if applies_to_type == "categories":
            cat_name = (product.get("category") or "").strip()
            if not cat_name:
                return False
            for cid in applies_to_value_ids:
                cat_name_cached = await self._get_category_name(cid)
                if cat_name_cached and cat_name_cached.strip() == cat_name:
                    return True
            return False
        if applies_to_type == "subCategories":
            sub = (product.get("subCategory") or "").strip()
            return sub in applies_to_value_ids if sub else False
        if applies_to_type == "brands":
            brand_name = (product.get("brand") or "").strip()
            if not brand_name:
                return False
            for bid in applies_to_value_ids:
                brand_name_cached = await self._get_brand_name(bid)
                if brand_name_cached and brand_name_cached.strip() == brand_name:
                    return True
            return False
        if applies_to_type == "collections":
            pid = str(product.get("_id", ""))
            if not pid:
                return False
            for cid in applies_to_value_ids:
                product_ids_cached = await self._get_collection_product_ids(cid)
                if product_ids_cached and pid in product_ids_cached:
                    return True
            return False
        if applies_to_type == "products":
            pid = str(product.get("_id", ""))
            return pid in [str(x) for x in applies_to_value_ids]
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

                    reference_date = datetime.utcnow()
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
                            # Check devices for app usage
                            device_storage = get_storage("deviceSubscriptions")
                            devices = await device_storage.findAll()
                            for d in devices:
                                if d.get("userId") and str(d.get("userId")) == str(user_id):
                                    has_app = True
                                    break
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

    async def create(self, coupon_data: Dict):
        method = coupon_data.get("method", "discount_code")
        code = coupon_data.get("code") or ""
        if method == "discount_code" and code:
            existing = await self.findByCode(code)
            if existing:
                raise ValueError("Discount code already exists")
            code = code.upper()
        elif method == "automatic":
            code = None  # no code for automatic

        applicable_roles = coupon_data.get("applicableRoles", ["customer"])
        prefix = "DISC-WH-" if "wholesaler" in applicable_roles else "DISC-RT-"

        # In simple array/json memory we can just filter
        # But motor query logic isn't always fully deterministic here if implemented purely as find
        # Let's get all coupons and manually find max to ensure safety across DBs
        all_coupons = await self.storage.findAll({})
        max_num = 0
        for doc in all_coupons:
            did = doc.get("displayId", "")
            if did.startswith(prefix):
                try:
                    num = int(did[len(prefix) :])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        display_id = f"{prefix}{max_num + 1}"

        coupon = {
            "typeOfDiscount": coupon_data.get("typeOfDiscount", "product_discount"),
            "code": code,
            "method": method,
            "discountType": coupon_data.get("discountType", "percentage"),
            "discountValue": float(coupon_data["discountValue"]),
            "minPurchaseAmount": float(coupon_data.get("minPurchaseAmount", 0)),
            "minRequirementType": coupon_data.get("minRequirementType", "none"),
            "minQuantityOfEligibleItems": int(coupon_data["minQuantityOfEligibleItems"])
            if coupon_data.get("minQuantityOfEligibleItems") is not None
            else None,
            "maxDiscountAmount": float(coupon_data["maxDiscountAmount"])
            if coupon_data.get("maxDiscountAmount")
            else None,
            "validFrom": coupon_data.get("validFrom", datetime.utcnow().isoformat()),
            "validUntil": coupon_data["validUntil"],
            "usageLimit": int(coupon_data["usageLimit"]) if coupon_data.get("usageLimit") else None,
            "usedCount": 0,
            "isActive": coupon_data.get("isActive", True),
            "applicableRoles": coupon_data.get("applicableRoles", ["customer"]),
            "applicableUserIds": coupon_data.get("applicableUserIds") or [],
            "applicableCategories": coupon_data.get("applicableCategories", []),
            "applicablePaymentMethods": coupon_data.get("applicablePaymentMethods", ["cod", "upi", "credit"]),
            "maxUsagePerUser": int(coupon_data["maxUsagePerUser"]) if coupon_data.get("maxUsagePerUser") else None,
            "userUsages": {},
            "appliesToType": coupon_data.get("appliesToType", "all"),
            "appliesToValueIds": coupon_data.get("appliesToValueIds") or [],
            "userBehavior": coupon_data.get("userBehavior") or None,
            "buyXGetYCustomerGetsQuantity": int(coupon_data["buyXGetYCustomerGetsQuantity"])
            if coupon_data.get("buyXGetYCustomerGetsQuantity")
            else None,
            "buyXGetYCustomerGetsAppliesToType": coupon_data.get("buyXGetYCustomerGetsAppliesToType"),
            "buyXGetYCustomerGetsAppliesToValueIds": coupon_data.get("buyXGetYCustomerGetsAppliesToValueIds") or [],
            "buyXGetYCustomerGetsDiscountType": coupon_data.get("buyXGetYCustomerGetsDiscountType"),
            "buyXGetYCustomerGetsDiscountValue": float(coupon_data["buyXGetYCustomerGetsDiscountValue"])
            if coupon_data.get("buyXGetYCustomerGetsDiscountValue") is not None
            else None,
            "displayId": display_id,
            "excludedProductIds": coupon_data.get("excludedProductIds") or [],
            "applicableItemType": coupon_data.get("applicableItemType") or "units",
            "couponMode": coupon_data.get("couponMode", "override"),
            "quantityTiers": [
                {"quantity": int(t["quantity"]), "discount": float(t["discount"])}
                for t in coupon_data["quantityTiers"]
            ] if coupon_data.get("quantityTiers") is not None else None,
        }

        # Handle Overlap
        resolution = coupon_data.get("resolution")
        force = coupon_data.get("force", False)

        if not force:
            overlap = await self.check_discount_overlap(coupon)
            if overlap:
                if resolution == "overwrite":
                    # Add exclusions to existing coupons
                    for detail in overlap["details"]:
                        existing_coupon = await self.findById(detail["couponId"])
                        if existing_coupon:
                            excl = set(existing_coupon.get("excludedProductIds") or [])
                            excl.update(detail["overlappingProductIds"])
                            await self.storage.update(detail["couponId"], {"excludedProductIds": list(excl)})
                elif resolution == "retain":
                    # Add exclusions to current coupon
                    excl = set(coupon.get("excludedProductIds") or [])
                    pids_to_exclude = set().union(*[set(d["overlappingProductIds"]) for d in overlap["details"]])
                    
                    # Check if all targeted products are excluded/covered
                    targeted_pids = await self._get_affected_product_ids(coupon)
                    if targeted_pids.issubset(pids_to_exclude):
                        raise ValueError("Discount not created because all targeted products are covered by retained earlier discounts")
                        
                    excl.update(list(pids_to_exclude))
                    coupon["excludedProductIds"] = list(excl)
                else:
                    raise OverlapConflictError(overlap)

        res = await self.storage.create(coupon)
        self.invalidate_cache()
        return res

    async def update(self, id: str, update_data: Dict):
        if "code" in update_data and update_data.get("code"):
            existing = await self.findByCode(update_data["code"])
            if existing and existing.get("_id") != id:
                raise ValueError("Discount code already in use")
            update_data["code"] = update_data["code"].upper()
        if update_data.get("method") == "automatic":
            update_data["code"] = None
        if "discountValue" in update_data:
            update_data["discountValue"] = float(update_data["discountValue"])
        if "minPurchaseAmount" in update_data:
            update_data["minPurchaseAmount"] = float(update_data["minPurchaseAmount"])
        if "minQuantityOfEligibleItems" in update_data and update_data["minQuantityOfEligibleItems"] is not None:
            update_data["minQuantityOfEligibleItems"] = int(update_data["minQuantityOfEligibleItems"])
        if "maxDiscountAmount" in update_data and update_data["maxDiscountAmount"]:
            update_data["maxDiscountAmount"] = float(update_data["maxDiscountAmount"])
        if "usageLimit" in update_data and update_data["usageLimit"]:
            update_data["usageLimit"] = int(update_data["usageLimit"])
        if "maxUsagePerUser" in update_data and update_data["maxUsagePerUser"]:
            update_data["maxUsagePerUser"] = int(update_data["maxUsagePerUser"])
        if "appliesToValueIds" in update_data and update_data["appliesToValueIds"] is None:
            update_data["appliesToValueIds"] = []
        if "applicableUserIds" in update_data and update_data["applicableUserIds"] is None:
            update_data["applicableUserIds"] = []
        if "buyXGetYCustomerGetsQuantity" in update_data and update_data["buyXGetYCustomerGetsQuantity"] is not None:
            update_data["buyXGetYCustomerGetsQuantity"] = int(update_data["buyXGetYCustomerGetsQuantity"])
        if (
            "buyXGetYCustomerGetsDiscountValue" in update_data
            and update_data["buyXGetYCustomerGetsDiscountValue"] is not None
        ):
            update_data["buyXGetYCustomerGetsDiscountValue"] = float(update_data["buyXGetYCustomerGetsDiscountValue"])
        if (
            "buyXGetYCustomerGetsAppliesToValueIds" in update_data
            and update_data["buyXGetYCustomerGetsAppliesToValueIds"] is None
        ):
            update_data["buyXGetYCustomerGetsAppliesToValueIds"] = []
        if "quantityTiers" in update_data and update_data["quantityTiers"] is not None:
            update_data["quantityTiers"] = [
                {"quantity": int(t.get("quantity")), "discount": float(t.get("discount"))}
                for t in update_data["quantityTiers"]
            ]

        # Handle Overlap
        resolution = update_data.get("resolution")
        force = update_data.get("force", False)

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
                    excl = set(update_data.get("excludedProductIds") or existing.get("excludedProductIds") or [])
                    pids_to_exclude = set().union(*[set(d["overlappingProductIds"]) for d in overlap["details"]])
                    
                    # Check if all targeted products are excluded/covered
                    targeted_pids = await self._get_affected_product_ids(full_data)
                    if targeted_pids.issubset(pids_to_exclude):
                        raise ValueError("Discount not updated because all targeted products are covered by retained earlier discounts")
                        
                    excl.update(list(pids_to_exclude))
                    update_data["excludedProductIds"] = list(excl)
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

        user_usages = coupon.get("userUsages", {})
        user_usages[user_id] = user_usages.get(user_id, 0) + 1

        return await self.update(id, {"usedCount": (coupon.get("usedCount", 0) or 0) + 1, "userUsages": user_usages})

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

        if not coupon.get("isActive", True):
            return {"valid": False, "message": "Discount is not active"}

        now = datetime.utcnow()
        valid_from = datetime.fromisoformat(coupon["validFrom"].replace("Z", "+00:00"))
        valid_until = datetime.fromisoformat(coupon["validUntil"].replace("Z", "+00:00"))

        if now < valid_from:
            return {"valid": False, "message": "Discount is not yet valid"}

        if now > valid_until:
            return {"valid": False, "message": "Discount has expired"}

        if coupon.get("usageLimit") and coupon.get("usedCount", 0) >= coupon["usageLimit"]:
            return {"valid": False, "message": "Discount usage limit reached"}

        if coupon.get("maxUsagePerUser"):
            user_usages = coupon.get("userUsages", {})
            if user_usages.get(user_id, 0) >= coupon["maxUsagePerUser"]:
                return {
                    "valid": False,
                    "message": f"You have reached the maximum usage limit ({coupon['maxUsagePerUser']}) for this discount",
                }

        if user_role not in coupon.get("applicableRoles", []):
            return {"valid": False, "message": "Discount not applicable for your role"}

        # Selective customers & User behavior segments check
        applicable_user_ids = coupon.get("applicableUserIds") or []
        user_behavior = coupon.get("userBehavior")
        has_specific_users = len(applicable_user_ids) > 0 or (user_behavior and user_behavior != "none")

        if has_specific_users:
            matches_selective = str(user_id) in [str(x) for x in applicable_user_ids]
            matches_behavior = await self._user_matches_behavior(user_id, user_behavior) if (user_behavior and user_behavior != "none") else False
            if not (matches_selective or matches_behavior):
                return {"valid": False, "message": "Discount not applicable for your account"}

        applicable_payment_methods = coupon.get("applicablePaymentMethods")
        if (
            applicable_payment_methods is not None
            and payment_method
            and payment_method.lower() not in [m.lower() for m in applicable_payment_methods]
        ):
            return {"valid": False, "message": f"Discount not applicable for {payment_method.upper()} payment method"}

        if coupon.get("typeOfDiscount") == "shipping_discount":
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
                allowed_pincodes = coupon.get("shippingPincodes") or []
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
            applies_to_type = coupon.get("appliesToType") or "all"
            applies_to_ids = coupon.get("appliesToValueIds") or []
            eligible_subtotal = 0.0
            for idx, item in enumerate(cart_items):
                product = await product_repository.findById(item.get("product") or item.get("productId"))
                if not product:
                    continue
                if await self._product_eligible_async(
                    product,
                    applies_to_type,
                    applies_to_ids if applies_to_ids else None,
                    coupon.get("excludedProductIds"),
                ):
                    qty = item.get("quantity", 0)
                    eligible_quantity += qty
                    sell_as_case = item.get("sellAsCase", False)
                    ignore_auto = (coupon.get("method") == "discount_code" and coupon.get("couponMode") == "override")
                    item_total = product_repository.calculateTotalPrice(
                        product, user_role, qty, sell_as_case=sell_as_case, user_id=user_id, ignore_auto_discount=ignore_auto
                    )
                    eligible_subtotal += item_total
                    eligible_item_indices.append(idx)
            purchase_amount_to_use = eligible_subtotal
        else:
            applicable_categories = coupon.get("applicableCategories", [])
            if applicable_categories and category and category not in applicable_categories:
                return {"valid": False, "message": "Discount not applicable for this category"}

        min_req = coupon.get("minRequirementType") or "none"
        if min_req == "min_amount" and purchase_amount_to_use < coupon.get("minPurchaseAmount", 0):
            return {
                "valid": False,
                "message": f"Minimum purchase amount of {coupon['minPurchaseAmount']} required (on eligible items)",
            }
        if min_req == "min_quantity":
            min_qty = coupon.get("minQuantityOfEligibleItems") or 0
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
        if coupon.get("typeOfDiscount") == "buy_x_get_y" and cart_items and product_repository:
            bxgy_res = await self._calculate_bxgy_discount(coupon, cart_items, product_repository, user_role, user_id)
            discount = bxgy_res["discount"]
            item_discounts = bxgy_res["itemDiscounts"]
            bxgy_item_indices = bxgy_res.get("bxgyItemIndices")
        elif coupon.get("typeOfDiscount") == "shipping_discount":
            if coupon["discountType"] == "percentage":
                discount = (shipping_charge * coupon["discountValue"]) / 100
                if coupon.get("maxDiscountAmount"):
                    discount = min(discount, coupon["maxDiscountAmount"])
            else:
                discount = coupon["discountValue"]
            discount = min(discount, shipping_charge)
        else:
            if coupon["discountType"] == "percentage":
                discount = (purchase_amount_to_use * coupon["discountValue"]) / 100
                if coupon.get("maxDiscountAmount"):
                    discount = min(discount, coupon["maxDiscountAmount"])
            else:
                if coupon.get("typeOfDiscount") == "product_discount":
                    discount = eligible_quantity * coupon["discountValue"]
                else:
                    discount = coupon["discountValue"]

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
    ) -> List[Dict]:
        """Find active automatic discounts that match user and cart. Returns list of { coupon, discount, eligibleItemIndices }."""
        now = datetime.utcnow()
        all_coupons = await self.storage.findAll({"method": "automatic", "isActive": True})
        results = []
        for coupon in all_coupons:
            try:
                if coupon.get("typeOfDiscount") == "product_discount":
                    continue
                valid_from = datetime.fromisoformat(coupon["validFrom"].replace("Z", "+00:00"))
                valid_until = datetime.fromisoformat(coupon["validUntil"].replace("Z", "+00:00"))
                if now < valid_from or now > valid_until:
                    continue
                if coupon.get("usageLimit") and (coupon.get("usedCount") or 0) >= coupon["usageLimit"]:
                    continue
                if user_role not in coupon.get("applicableRoles", []):
                    continue
                applicable_user_ids = coupon.get("applicableUserIds") or []
                user_behavior = coupon.get("userBehavior")
                has_specific_users = len(applicable_user_ids) > 0 or (user_behavior and user_behavior != "none")

                if has_specific_users:
                    matches_selective = str(user_id) in [str(x) for x in applicable_user_ids]
                    matches_behavior = await self._user_matches_behavior(user_id, user_behavior) if (user_behavior and user_behavior != "none") else False
                    if not (matches_selective or matches_behavior):
                        continue
                if payment_method:
                    applicable_payment_methods = coupon.get("applicablePaymentMethods")
                    if applicable_payment_methods is not None and payment_method.lower() not in [
                        m.lower() for m in applicable_payment_methods
                    ]:
                        continue

                if coupon.get("typeOfDiscount") == "shipping_discount":
                    addr = shipping_address
                    if not addr:
                        from app.repositories.user_repository import user_repository

                        u = await user_repository.findById(user_id)
                        if u and u.get("address"):
                            addr = u.get("address")

                    if addr:
                        pincode = addr.get("zipCode") or addr.get("pincode")
                        if not pincode:
                            continue
                        allowed_pincodes = coupon.get("shippingPincodes") or []
                        if allowed_pincodes and str(pincode).strip() not in [str(p).strip() for p in allowed_pincodes]:
                            continue
                    else:
                        continue
                # Compute eligible subtotal and quantity
                applies_to_type = coupon.get("appliesToType") or "all"
                applies_to_ids = coupon.get("appliesToValueIds") or []
                eligible_subtotal = 0.0
                eligible_quantity = 0
                eligible_item_indices = []
                for idx, item in enumerate(cart_items):
                    product = await product_repository.findById(item.get("product") or item.get("productId"))
                    if not product:
                        continue
                    if await self._product_eligible_async(
                        product,
                        applies_to_type,
                        applies_to_ids if applies_to_ids else None,
                        coupon.get("excludedProductIds"),
                    ):
                        qty = item.get("quantity", 0)
                        eligible_quantity += qty
                        sell_as_case = item.get("sellAsCase", False)
                        item_total = product_repository.calculateTotalPrice(
                            product, user_role, qty, sell_as_case=sell_as_case, user_id=user_id
                        )
                        eligible_subtotal += item_total
                        eligible_item_indices.append(idx)
                min_req = coupon.get("minRequirementType") or "none"
                if min_req == "min_amount" and eligible_subtotal < coupon.get("minPurchaseAmount", 0):
                    continue
                if min_req == "min_quantity":
                    min_qty = coupon.get("minQuantityOfEligibleItems") or 0
                    if eligible_quantity < min_qty:
                        continue
                if coupon.get("maxUsagePerUser"):
                    user_usages = coupon.get("userUsages", {})
                    if user_usages.get(user_id, 0) >= coupon["maxUsagePerUser"]:
                        continue
                discount = 0.0
                item_discounts = None
                bxgy_item_indices = None
                if coupon.get("typeOfDiscount") == "buy_x_get_y":
                    bxgy_res = await self._calculate_bxgy_discount(coupon, cart_items, product_repository, user_role, user_id)
                    discount = bxgy_res["discount"]
                    item_discounts = bxgy_res["itemDiscounts"]
                    bxgy_item_indices = bxgy_res.get("bxgyItemIndices")
                elif coupon.get("typeOfDiscount") == "shipping_discount":
                    if coupon["discountType"] == "percentage":
                        discount = (shipping_charge * coupon["discountValue"]) / 100
                        if coupon.get("maxDiscountAmount"):
                            discount = min(discount, coupon["maxDiscountAmount"])
                    else:
                        discount = coupon["discountValue"]
                    discount = min(discount, shipping_charge)
                else:
                    if coupon["discountType"] == "percentage":
                        discount = (eligible_subtotal * coupon["discountValue"]) / 100
                        if coupon.get("maxDiscountAmount"):
                            discount = min(discount, coupon["maxDiscountAmount"])
                    else:
                        if coupon.get("typeOfDiscount") == "product_discount":
                            discount = eligible_quantity * coupon["discountValue"]
                        else:
                            discount = coupon["discountValue"]
                results.append(
                    {
                        "coupon": coupon,
                        "discount": round(discount, 2),
                        "eligibleItemIndices": eligible_item_indices,
                        "itemDiscounts": item_discounts,
                        "bxgyItemIndices": bxgy_item_indices
                    }
                )
            except Exception:
                continue
        return results

    async def _get_affected_product_ids(self, coupon_data: Dict) -> set:
        """Expand appliesToType/ValueIds into a set of product IDs."""
        applies_to_type = coupon_data.get("appliesToType") or "all"
        applies_to_value_ids = coupon_data.get("appliesToValueIds") or []
        excluded_product_ids = set(str(x) for x in (coupon_data.get("excludedProductIds") or []))

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
                if brand and brand.get("name"):
                    eligible_brand_names.add(brand.get("name").strip())
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
            pid = str(p.get("_id", ""))
            if pid in excluded_product_ids:
                continue

            if applies_to_type == "all":
                affected.add(pid)
            elif applies_to_type == "categories":
                p_cat = (p.get("category") or "").strip().lower()
                if p_cat and p_cat in {c.lower() for c in eligible_category_names}:
                    affected.add(pid)
            elif applies_to_type == "subCategories":
                p_sub = (p.get("subCategory") or "").strip()
                if p_sub and p_sub in applies_to_value_ids:
                    affected.add(pid)
            elif applies_to_type == "brands":
                p_brand = (p.get("brand") or "").strip().lower()
                if p_brand and p_brand in {b.lower() for b in eligible_brand_names}:
                    affected.add(pid)

        return affected

    async def check_discount_overlap(self, coupon_data: Dict, exclude_coupon_id: Optional[str] = None):
        """Identify conflicting active coupons and return affected product count."""
        if not coupon_data.get("isActive", True):
            return None

        roles = coupon_data.get("applicableRoles") or []
        all_coupons = await self.storage.findAll({"isActive": True})

        # Filter for same roles
        conflicting_candidates = [
            c
            for c in all_coupons
            if any(r in (c.get("applicableRoles") or []) for r in roles) and str(c.get("_id")) != str(exclude_coupon_id)
        ]

        new_affected_ids = await self._get_affected_product_ids(coupon_data)
        type_of_discount = coupon_data.get("typeOfDiscount") or "product_discount"
        
        if type_of_discount == "buy_x_get_y":
            gy_applies_to_type = coupon_data.get("buyXGetYCustomerGetsAppliesToType", "all")
            gy_applies_to_ids = coupon_data.get("buyXGetYCustomerGetsAppliesToValueIds") or []
            dummy_gy_coupon = {"appliesToType": gy_applies_to_type, "appliesToValueIds": gy_applies_to_ids, "excludedProductIds": coupon_data.get("excludedProductIds")}
            gy_affected_ids = await self._get_affected_product_ids(dummy_gy_coupon)
            new_affected_ids = new_affected_ids.union(gy_affected_ids)

        if not new_affected_ids:
            return None

        applicable_item_type = coupon_data.get("applicableItemType") or "units"

        overlaps = []
        for c in conflicting_candidates:
            c_type = c.get("typeOfDiscount") or "product_discount"
            if c_type != type_of_discount:
                continue

            is_bxgy = type_of_discount == "buy_x_get_y"
            c_affected_ids = await self._get_affected_product_ids(c)
            if is_bxgy:
                c_gy_applies_to_type = c.get("buyXGetYCustomerGetsAppliesToType", "all")
                c_gy_applies_to_ids = c.get("buyXGetYCustomerGetsAppliesToValueIds") or []
                c_dummy_gy = {"appliesToType": c_gy_applies_to_type, "appliesToValueIds": c_gy_applies_to_ids, "excludedProductIds": c.get("excludedProductIds")}
                c_gy_affected_ids = await self._get_affected_product_ids(c_dummy_gy)
                c_affected_ids = c_affected_ids.union(c_gy_affected_ids)
            else:
                # Amount off/Shipping/Total discount logic
                # For Business segment, check if applicableItemType (units/cases) matches
                if "wholesaler" in roles:
                    if (c.get("applicableItemType") or "units") != applicable_item_type:
                        continue

            intersection = new_affected_ids.intersection(c_affected_ids)

            if intersection:
                overlaps.append(
                    {
                        "couponId": str(c["_id"]),
                        "displayId": c.get("displayId"),
                        "overlappingProductIds": list(intersection),
                    }
                )

        if overlaps:
            total_overlapping_products = len(set().union(*[set(o["overlappingProductIds"]) for o in overlaps]))
            return {"totalOverlappingProducts": total_overlapping_products, "details": overlaps}
        return None

    async def get_active_coupons(self) -> List[Dict]:
        """Get all active coupons with a short 60s cache"""
        now = datetime.utcnow()
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

    async def get_active_automatic_product_discounts(self) -> List[Dict]:
        """Get all active automatic product discounts with short caching"""
        now = datetime.utcnow()
        if (
            self._active_automatic_discounts_cache is not None
            and self._active_automatic_discounts_cache_time
            and (now - self._active_automatic_discounts_cache_time).total_seconds() < 300
        ):
            return self._active_automatic_discounts_cache
        
        discounts = await self.storage.findAll({
            "method": "automatic",
            "isActive": True,
            "typeOfDiscount": "product_discount"
        })
        
        valid_discounts = []
        for c in discounts:
            try:
                valid_from = datetime.fromisoformat(c["validFrom"].replace("Z", "+00:00")).replace(tzinfo=None)
                valid_until = datetime.fromisoformat(c["validUntil"].replace("Z", "+00:00")).replace(tzinfo=None)
                if valid_from <= now <= valid_until:
                    c["_affected_product_ids"] = await self._get_affected_product_ids(c)
                    valid_discounts.append(c)
            except Exception:
                continue
                
        self._active_automatic_discounts_cache = valid_discounts
        self._active_automatic_discounts_cache_time = now
        return valid_discounts

    async def get_applicable_automatic_product_discounts(self, role: str, user_id: Optional[str] = None) -> List[Dict]:
        discounts = await self.get_active_automatic_product_discounts()
        applicable = []
        for c in discounts:
            if role not in c.get("applicableRoles", []):
                continue
            applicable_user_ids = c.get("applicableUserIds") or []
            if applicable_user_ids:
                if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                    continue
            behavior = c.get("userBehavior")
            if behavior and behavior != "none":
                if not user_id or not await self._user_matches_behavior(user_id, behavior):
                    continue
            applicable.append(c)
        return applicable

    async def get_applicable_discounts_for_product(
        self,
        product: Dict,
        role: str,
        user_id: Optional[str] = None,
        all_coupons: Optional[List[Dict]] = None,
        user_behavior_cache: Optional[Dict] = None,
    ) -> List[Dict]:
        """Find other active discounts applicable to this product, excluding the default highest automatic product discount"""
        if all_coupons is None:
            all_coupons = await self.get_active_coupons()
        
        now = datetime.utcnow()
        default_auto_discount = None
        highest_pct = -1.0
        
        # Step 1: Find the default highest automatic product discount
        for c in all_coupons:
            try:
                valid_from = datetime.fromisoformat(c["validFrom"].replace("Z", "+00:00")).replace(tzinfo=None)
                valid_until = datetime.fromisoformat(c["validUntil"].replace("Z", "+00:00")).replace(tzinfo=None)
                if not (valid_from <= now <= valid_until):
                    continue
            except Exception:
                continue
                
            if c.get("method") == "automatic" and c.get("typeOfDiscount") == "product_discount":
                if role in c.get("applicableRoles", []):
                    is_eligible = await self._product_eligible_async(
                        product,
                        c.get("appliesToType", "all"),
                        c.get("appliesToValueIds"),
                        c.get("excludedProductIds")
                    )
                    if is_eligible:
                        applicable_user_ids = c.get("applicableUserIds") or []
                        if applicable_user_ids and (not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]):
                            continue
                        behavior = c.get("userBehavior")
                        if behavior and behavior != "none" and (not user_id or not await self._user_matches_behavior(user_id, behavior, user_behavior_cache=user_behavior_cache)):
                            continue
                            
                        pct = 0.0
                        if c.get("discountType") == "percentage":
                            pct = float(c.get("discountValue") or 0)
                        elif c.get("discountType") == "fixed":
                            mrp = float(product.get("mrp") or 0)
                            if mrp > 0:
                                pct = (float(c.get("discountValue") or 0) / mrp) * 100
                        if pct > highest_pct:
                            highest_pct = pct
                            default_auto_discount = c
                            
        # Step 2: Gather all other applicable coupons
        applicable = []
        for c in all_coupons:
            if default_auto_discount and str(c.get("_id")) == str(default_auto_discount.get("_id")):
                continue
                
            try:
                valid_from = datetime.fromisoformat(c["validFrom"].replace("Z", "+00:00")).replace(tzinfo=None)
                valid_until = datetime.fromisoformat(c["validUntil"].replace("Z", "+00:00")).replace(tzinfo=None)
                if not (valid_from <= now <= valid_until):
                    continue
            except Exception:
                continue
                
            if role not in c.get("applicableRoles", []):
                continue
                
            applicable_user_ids = c.get("applicableUserIds") or []
            if applicable_user_ids and (not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]):
                continue
            behavior = c.get("userBehavior")
            if behavior and behavior != "none" and (not user_id or not await self._user_matches_behavior(user_id, behavior, user_behavior_cache=user_behavior_cache)):
                continue
                
            applies = True
            if c.get("typeOfDiscount") in ["product_discount", "buy_x_get_y"]:
                applies = await self._product_eligible_async(
                    product,
                    c.get("appliesToType", "all"),
                    c.get("appliesToValueIds"),
                    c.get("excludedProductIds")
                )
                
            if applies:
                applicable.append(c)
                
        return applicable


def get_coupon_description(c: Dict) -> str:
    method_lbl = "Use code " + c["code"] if c.get("method") == "discount_code" and c.get("code") else "Automatic offer"
    type_of_disc = c.get("typeOfDiscount")
    disc_type = c.get("discountType")
    disc_val = c.get("discountValue")
    
    if type_of_disc == "product_discount":
        if c.get("minRequirementType") == "quantity_based" and c.get("quantityTiers"):
            tiers = sorted(c["quantityTiers"], key=lambda x: x["quantity"])
            item_lbl = c.get("applicableItemType", "units")
            tier_strs = [f"Buy {t['quantity']}+ {item_lbl} get {t['discount']}% off" for t in tiers]
            return f"{method_lbl}: " + ", ".join(tier_strs) + " per unit."
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off on eligible items."
    elif type_of_disc == "buy_x_get_y":
        min_qty = c.get("minQuantityOfEligibleItems") or 1
        gets_qty = c.get("buyXGetYCustomerGetsQuantity") or 1
        gets_type = c.get("buyXGetYCustomerGetsDiscountType")
        gets_val = c.get("buyXGetYCustomerGetsDiscountValue")
        
        gets_desc = "Free"
        if gets_type == "percentage":
            gets_desc = f"{gets_val}% Off"
        elif gets_type == "amount_off":
            gets_desc = f"₹{gets_val} Off"
            
        return f"{method_lbl}: Buy {min_qty} unit(s) and get {gets_qty} unit(s) at {gets_desc}."
    elif type_of_disc == "total_order_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        min_amt = c.get("minPurchaseAmount") or 0
        min_str = f" on orders above ₹{min_amt}" if min_amt > 0 else ""
        return f"{method_lbl}: Get {val_str} off total order{min_str}."
    elif type_of_disc == "shipping_discount":
        val_str = f"{disc_val}%" if disc_type == "percentage" else f"₹{disc_val}"
        return f"{method_lbl}: Get {val_str} off shipping charges."
    else:
        return f"{method_lbl} available."


coupon_repository = CouponRepository()
