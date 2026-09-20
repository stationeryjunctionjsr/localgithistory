import re

with open('app/repositories/coupon_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

repo_repl = '''
            appliesToValueIds=coupon_data.appliesToValueIds or [],
            excludedProductIds=coupon_data.excludedProductIds or [],
            quantityTiers=qt_list,
            displayId=display_id,
            buyXGetYCustomerGetsAppliesToValueIds=coupon_data.buyXGetYCustomerGetsAppliesToValueIds or [],
            buyXGetYCustomerGetsDiscountType=coupon_data.buyXGetYCustomerGetsDiscountType,
            buyXGetYCustomerGetsDiscountValue=float(coupon_data.buyXGetYCustomerGetsDiscountValue) if coupon_data.buyXGetYCustomerGetsDiscountValue is not None else None,
            applicableItemType=coupon_data.applicableItemType or "units",
            couponMode=coupon_data.couponMode or "override",
            maxUsagePerUser=int(coupon_data.maxUsagePerUser) if coupon_data.maxUsagePerUser else None,
            userBehavior=coupon_data.userBehavior,
        )
'''

text = re.sub(
    r'            appliesToValueIds=coupon_data\.appliesToValueIds or \[\],\s*excludedProductIds=coupon_data\.excludedProductIds or \[\],\s*quantityTiers=qt_list,\s*\)',
    repo_repl.strip(),
    text
)

# And fix incrementUsage
inc_repl = '''
    async def incrementUsage(self, id: str, user_id: str):
        coupon = await self.findById(id)
        if not coupon:
            return None

        # coupon is a CouponInternal object now
        user_usages = coupon.userUsages if getattr(coupon, "userUsages", None) else {}
        user_usages[user_id] = user_usages.get(user_id, 0) + 1

        return await self.update(id, {"usedCount": (getattr(coupon, "usedCount", 0) or 0) + 1, "userUsages": user_usages})
'''

text = re.sub(
    r'    async def incrementUsage\(self, id: str, user_id: str\):.*?return await self\.update\(id, \{"usedCount": \(coupon\.get\("usedCount", 0\) or 0\) \+ 1, "userUsages": user_usages\}\)',
    inc_repl.strip(),
    text,
    flags=re.DOTALL
)

with open('app/repositories/coupon_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
