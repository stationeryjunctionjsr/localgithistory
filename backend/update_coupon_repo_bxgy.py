import re

with open('app/repositories/coupon_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix usageLimit -> maxUses
text = text.replace('coupon.usageLimit', 'coupon.maxUses')

# Fix coupon['maxUsagePerUser'] -> coupon.maxUsagePerUser
text = text.replace("coupon['maxUsagePerUser']", "coupon.maxUsagePerUser")

# Fix missing applicablePaymentMethods? Wait, let's just make it getattr
text = re.sub(
    r'applicable_payment_methods = \(coupon\.applicablePaymentMethods if coupon\.applicablePaymentMethods is not None else None\)',
    'applicable_payment_methods = (getattr(coupon, "applicablePaymentMethods", None))',
    text
)

# And fix BXGY checks in check_discount_overlap
bxgy_repl1 = '''
            gy_applies_to_type = getattr(coupon_data, "buyXGetYCustomerGetsAppliesToType", "all")
            gy_applies_to_ids = getattr(coupon_data, "buyXGetYCustomerGetsAppliesToValueIds", []) or []
            dummy_gy_coupon = CouponInternalCreate(
                appliesToType=gy_applies_to_type,
                appliesToValueIds=gy_applies_to_ids,
                excludedProductIds=getattr(coupon_data, "excludedProductIds", []),
            )
'''

text = re.sub(
    r'            gy_applies_to_type = coupon_data\.get\("buyXGetYCustomerGetsAppliesToType", "all"\)\s*gy_applies_to_ids = coupon_data\.get\("buyXGetYCustomerGetsAppliesToValueIds"\) or \[\]\s*dummy_gy_coupon = \{\s*"appliesToType": gy_applies_to_type,\s*"appliesToValueIds": gy_applies_to_ids,\s*"excludedProductIds": coupon_data\.get\("excludedProductIds"\),\s*\}',
    bxgy_repl1.strip(),
    text
)

bxgy_repl2 = '''
                c_gy_applies_to_type = getattr(c, "buyXGetYCustomerGetsAppliesToType", "all")
                c_gy_applies_to_ids = getattr(c, "buyXGetYCustomerGetsAppliesToValueIds", []) or []
                c_dummy_gy = CouponInternalCreate(
                    appliesToType=c_gy_applies_to_type,
                    appliesToValueIds=c_gy_applies_to_ids,
                    excludedProductIds=getattr(c, "excludedProductIds", []),
                )
'''

text = re.sub(
    r'                c_gy_applies_to_type = c\.get\("buyXGetYCustomerGetsAppliesToType", "all"\)\s*c_gy_applies_to_ids = c\.get\("buyXGetYCustomerGetsAppliesToValueIds"\) or \[\]\s*c_dummy_gy = \{\s*"appliesToType": c_gy_applies_to_type,\s*"appliesToValueIds": c_gy_applies_to_ids,\s*"excludedProductIds": c\.get\("excludedProductIds"\),\s*\}',
    bxgy_repl2.strip(),
    text
)

# And replace c.get in check_discount_overlap with getattr
text = re.sub(r'c\.get\("typeOfDiscount"\)', 'getattr(c, "typeOfDiscount", None)', text)
text = re.sub(r'c\.get\("applicableItemType"\)', 'getattr(c, "applicableItemType", None)', text)


with open('app/repositories/coupon_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
