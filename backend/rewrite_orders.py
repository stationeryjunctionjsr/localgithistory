import re

content = open('c:/Ecommerce app/backend/app/routers/orders.py', encoding='utf-8').read()

start_marker = "    # Build item totals for discount distribution (eligible-only vs all)"
end_marker = "    # -------------------------------"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    exit(1)

new_block = """    # Build item totals for discount distribution (eligible-only vs all)
    initial_subtotal = 0.0
    eligible_subtotal_for_discount = None
    item_totals = []
    for idx, item in enumerate(cart_items):
        product = await product_repository.findById(item.get("product") or item.get("productId"))
        if not product:
            raise HTTPException(
                status_code=400, detail=f"Product not found: {item.get('product') or item.get('productId')}"
            )
        quantity = item.get("quantity", 0)
        sell_as_case = item.get("sellAsCase", False)
        
        ignore_auto = False
        if is_override and eligible_item_indices is not None and idx in eligible_item_indices:
            ignore_auto = True
            
        item_total = product_repository.calculateTotalPrice(
            product, effective_role, quantity, sell_as_case=sell_as_case, user_id=current_user.get("_id"), ignore_auto_discount=ignore_auto
        )
        item_totals.append((product, item_total, quantity, sell_as_case, item))
        initial_subtotal += item_total
    if eligible_item_indices is not None and len(eligible_item_indices) > 0 and coupon_discount > 0:
        eligible_subtotal_for_discount = sum(item_totals[i][1] for i in eligible_item_indices if i < len(item_totals))

    # --- Phase 1: Apply Coupon Discount ---
    for idx, (product, item_total_before_coupon, quantity, sell_as_case, item) in enumerate(item_totals):
        # Apply discount: exact mapping if available, else proportional
        if item_discounts is not None and idx in item_discounts:
            item_coupon_discount = item_discounts[idx]
            item_discounts[idx] = 0.0 # Prevent double application if any logic loops
        elif (
            coupon_discount > 0
            and eligible_subtotal_for_discount
            and eligible_subtotal_for_discount > 0
            and idx in (eligible_item_indices or [])
        ):
            coupon_discount_ratio = coupon_discount / eligible_subtotal_for_discount
            item_coupon_discount = item_total_before_coupon * coupon_discount_ratio
        elif coupon_discount > 0 and initial_subtotal > 0:
            coupon_discount_ratio = coupon_discount / initial_subtotal
            item_coupon_discount = item_total_before_coupon * coupon_discount_ratio
        else:
            item_coupon_discount = 0.0
            
        item_total_after_coupon = max(0.0, item_total_before_coupon - item_coupon_discount)
        
        # Store temporary values back in the tuple (re-constructing the tuple)
        item_totals[idx] = (product, item_total_before_coupon, quantity, sell_as_case, item, item_coupon_discount, item_total_after_coupon)

    # --- Phase 2: Compute global referral discount ---
    subtotal_after_coupon = sum(t[6] for t in item_totals)
    
    referral_discount = 0.0
    applied_referral_code = None

    if hasattr(order_data, "referralCode") and order_data.referralCode:
        ref_code = order_data.referralCode.strip().upper()
        
        # 1. User must be customer role (Retail)
        if effective_role != "customer":
            raise HTTPException(
                status_code=400,
                detail="Referral discount is only available for retail customers"
            )
            
        # 2. Must be first order (0 orders)
        order_count = await order_repository.countByUser(current_user.get("_id"))
        if order_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Referral discount is only available on your first order"
            )
            
        # 3. Settings must be active globally
        from app.repositories.referral_repository import referral_repository
        ref_settings = await referral_repository.get_settings()
        retail_settings = ref_settings.get("retail", {})
        if not retail_settings.get("isActive", False) or retail_settings.get("discountValue", 0) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Referral program is not active at the moment"
            )
            
        # 4. Valid referrer user
        referrer = await user_repository.findOne({"referralCode": ref_code})
        if not referrer:
            raise HTTPException(
                status_code=400,
                detail="Invalid referral code"
            )
            
        # 5. Cannot refer self
        if str(referrer.get("_id")) == str(current_user.get("_id")):
            raise HTTPException(
                status_code=400,
                detail="You cannot use your own referral code"
            )
            
        # If all valid, calculate discount using latest settings
        discount_type = retail_settings.get("discountType")
        discount_value = retail_settings.get("discountValue", 0)
        
        if discount_type == "percentage":
            referral_discount = subtotal_after_coupon * (discount_value / 100)
        else: # fixed
            referral_discount = min(discount_value, subtotal_after_coupon)
            
        applied_referral_code = ref_code
    # -------------------------------

    # --- Phase 3: Distribute referral discount, calculate single unit price & GST ---
    subtotal = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    order_items = []

    for idx, (product, item_total_before_coupon, quantity, sell_as_case, item, item_coupon_discount, item_total_after_coupon) in enumerate(item_totals):
        
        # Distribute referral discount proportionally
        if referral_discount > 0 and subtotal_after_coupon > 0:
            item_referral_discount = item_total_after_coupon * (referral_discount / subtotal_after_coupon)
        else:
            item_referral_discount = 0.0
            
        final_item_total = max(0.0, item_total_after_coupon - item_referral_discount)
        
        # Calculate total single physical units
        qty_per_case = int(product.get("quantityPerCase") or 1)
        total_single_units = (quantity * qty_per_case) if sell_as_case else quantity
        
        single_unit_price = final_item_total / total_single_units if total_single_units > 0 else 0.0
        
        # GST Calculation per single unit
        gst_percent = product.get("gst", 0) if gst_enabled else 0
        gst_multiplier = 1 + (gst_percent / 100)
        single_unit_taxable_value = single_unit_price / gst_multiplier if gst_multiplier > 0 else single_unit_price
        single_unit_cgst = single_unit_taxable_value * (gst_percent / 200) if gst_percent > 0 else 0
        single_unit_sgst = single_unit_taxable_value * (gst_percent / 200) if gst_percent > 0 else 0
        
        # Aggregate totals for the item
        taxable_value = single_unit_taxable_value * total_single_units
        cgst = single_unit_cgst * total_single_units
        sgst = single_unit_sgst * total_single_units

        subtotal += final_item_total
        total_cgst += cgst
        total_sgst += sgst

        effective_price = (item_total_before_coupon / quantity) if quantity else 0

        order_items.append(
            {
                "product": product.get("_id"),
                "quantity": quantity,
                "sellAsCase": sell_as_case,
                "price": effective_price,
                "priceBeforeCoupon": round(item_total_before_coupon, 2),
                "couponDiscount": round(item_coupon_discount, 2),
                "referralDiscount": round(item_referral_discount, 2),
                "subtotal": round(final_item_total, 2),
                "singleUnitPrice": round(single_unit_price, 2),
                "singleUnitTaxableValue": round(single_unit_taxable_value, 2),
                "singleUnitCGST": round(single_unit_cgst, 2),
                "singleUnitSGST": round(single_unit_sgst, 2),
                "numberOfSingleUnits": total_single_units,
                "gst": gst_percent,
                "taxableValue": round(taxable_value, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
            }
        )

        # Check stock (considering reservations)
        from app.repositories.stock_reservation_repository import stock_reservation_repository
        user_res = await stock_reservation_repository.get_user_reservations(current_user["_id"])
        prod_res = next((r for r in user_res if r.get("productId") == str(product.get("_id"))), None)

        has_valid_reservation = False
        if prod_res and int(prod_res.get("quantity", 0)) >= quantity:
            has_valid_reservation = True

        if not has_valid_reservation:
            # Check if stock is available in the pool
            available_pool = await product_repository.get_available_stock(
                product.get("_id"), exclude_user_id=current_user["_id"]
            )
            if available_pool < quantity:
                ORDER_FAILURES.labels(reason="insufficient_stock").inc()
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock is no longer reserved or available for {product.get('name')}. Please check your cart.",
                )

    tax = round(total_cgst + total_sgst, 2)  # Total GST = CGST + SGST
"""

new_content = content[:start_idx] + new_block + content[end_idx:]

with open('c:/Ecommerce app/backend/app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated orders.py successfully")
