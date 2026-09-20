import re

with open('app/models/daos_flat.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''    appliesToType: Optional[str] = None
    
    displayId: Optional[str] = None
    buyXGetYCustomerGetsAppliesToValueIds: Optional[List[str]] = None
    buyXGetYCustomerGetsDiscountType: Optional[str] = None
    buyXGetYCustomerGetsDiscountValue: Optional[float] = None
    applicableItemType: Optional[str] = None
    couponMode: Optional[str] = None
    maxUsagePerUser: Optional[int] = None
    userUsages: Optional[Dict[str, int]] = None
    userBehavior: Optional[str] = None
'''

# Update CouponInternal
text = re.sub(r'    appliesToType: Optional\[str\] = None(?=\s+quantityTiers)', replacement, text)

with open('app/models/daos_flat.py', 'w', encoding='utf-8') as f:
    f.write(text)
