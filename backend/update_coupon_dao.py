import re

with open('app/db/mysql_coupons_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update create method params
create_repl = '''
        if data.displayId is not None:
            cols.append("display_id")
            params["s_displayId"] = data.displayId

        if data.buyXGetYCustomerGetsAppliesToValueIds is not None:
            cols.append("bxgy_applies_to_ids")
            params["s_bxgy_applies_to_ids"] = json.dumps(data.buyXGetYCustomerGetsAppliesToValueIds)

        if data.buyXGetYCustomerGetsDiscountType is not None:
            cols.append("bxgy_discount_type")
            params["s_bxgy_discount_type"] = data.buyXGetYCustomerGetsDiscountType

        if data.buyXGetYCustomerGetsDiscountValue is not None:
            cols.append("bxgy_discount_value")
            params["s_bxgy_discount_value"] = data.buyXGetYCustomerGetsDiscountValue

        if data.applicableItemType is not None:
            cols.append("applicable_item_type")
            params["s_applicable_item_type"] = data.applicableItemType

        if data.couponMode is not None:
            cols.append("coupon_mode")
            params["s_coupon_mode"] = data.couponMode

        if data.maxUsagePerUser is not None:
            cols.append("max_usage_per_user")
            params["s_max_usage_per_user"] = data.maxUsagePerUser

        if data.userUsages is not None:
            cols.append("user_usages")
            params["s_user_usages"] = json.dumps(data.userUsages)

        if data.userBehavior is not None:
            cols.append("user_behavior")
            params["s_user_behavior"] = data.userBehavior

        col_sql = ", ".join(cols)
'''

text = re.sub(r'        col_sql = ", "\.join\(cols\)', create_repl.strip(), text, count=1)


# Update update method params
update_repl = '''
        if data.displayId is not None:
            set_clauses.append("display_id = :s_displayId")
            params["s_displayId"] = data.displayId

        if data.buyXGetYCustomerGetsAppliesToValueIds is not None:
            set_clauses.append("bxgy_applies_to_ids = :s_bxgy_applies_to_ids")
            params["s_bxgy_applies_to_ids"] = json.dumps(data.buyXGetYCustomerGetsAppliesToValueIds)

        if data.buyXGetYCustomerGetsDiscountType is not None:
            set_clauses.append("bxgy_discount_type = :s_bxgy_discount_type")
            params["s_bxgy_discount_type"] = data.buyXGetYCustomerGetsDiscountType

        if data.buyXGetYCustomerGetsDiscountValue is not None:
            set_clauses.append("bxgy_discount_value = :s_bxgy_discount_value")
            params["s_bxgy_discount_value"] = data.buyXGetYCustomerGetsDiscountValue

        if data.applicableItemType is not None:
            set_clauses.append("applicable_item_type = :s_applicable_item_type")
            params["s_applicable_item_type"] = data.applicableItemType

        if data.couponMode is not None:
            set_clauses.append("coupon_mode = :s_coupon_mode")
            params["s_coupon_mode"] = data.couponMode

        if data.maxUsagePerUser is not None:
            set_clauses.append("max_usage_per_user = :s_max_usage_per_user")
            params["s_max_usage_per_user"] = data.maxUsagePerUser

        if data.userUsages is not None:
            set_clauses.append("user_usages = :s_user_usages")
            params["s_user_usages"] = json.dumps(data.userUsages)

        if data.userBehavior is not None:
            set_clauses.append("user_behavior = :s_user_behavior")
            params["s_user_behavior"] = data.userBehavior

        if not set_clauses:
'''

text = re.sub(r'        if not set_clauses:', update_repl.strip(), text, count=1)


# Update _row_to_doc
row_repl = '''
            "appliesToType": r.applies_to_type,
            "displayId": getattr(r, "display_id", None),
            "buyXGetYCustomerGetsAppliesToValueIds": json.loads(r.bxgy_applies_to_ids) if getattr(r, "bxgy_applies_to_ids", None) else None,
            "buyXGetYCustomerGetsDiscountType": getattr(r, "bxgy_discount_type", None),
            "buyXGetYCustomerGetsDiscountValue": float(r.bxgy_discount_value) if getattr(r, "bxgy_discount_value", None) is not None else None,
            "applicableItemType": getattr(r, "applicable_item_type", None),
            "couponMode": getattr(r, "coupon_mode", None),
            "maxUsagePerUser": int(r.max_usage_per_user) if getattr(r, "max_usage_per_user", None) is not None else None,
            "userUsages": json.loads(r.user_usages) if getattr(r, "user_usages", None) else None,
            "userBehavior": getattr(r, "user_behavior", None),
        }
'''

text = re.sub(r'            "appliesToType": r\.applies_to_type,\s*\}', row_repl.strip(), text)


# Make sure json is imported
if 'import json' not in text:
    text = "import json\n" + text

with open('app/db/mysql_coupons_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
