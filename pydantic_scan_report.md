# Pydantic Anti-Pattern Scan Report

## hasattr (125 hits)
`
clean_orders.py:22: oid = str(p.orderId) if hasattr(p, "orderId") else str(getattr(p, "order_id", getattr(p, "orderId", None)))
fix_ad.py:80: if hasattr(data, api_k) and getattr(data, api_k) is not None:
fix_ad.py:89: if hasattr(data, "stats") and data.stats is not None:
fix_ad.py:91: if hasattr(data.stats, api_k) and getattr(data.stats, api_k) is not None:
fix_analytics.py:7: old_code = """        raw_dict = event.payload.root if hasattr(event.payload, "root") else (event.payload if isinstance(event.payload, dict) else {})
fix_analytics.py:10: new_code = """        raw_dict = event.payload.model_dump(exclude_unset=True) if hasattr(event.payload, 'model_dump') else (event.payload.root if hasattr(event.payload, "root") else (event.payload if isinstance(event.payload, dict) else {}))
fix_analytics.py:16: old_code_2 = """        raw_payload_dict = raw_payload.root if hasattr(raw_payload, "root") else (raw_payload if isinstance(raw_payload, dict) else {})
fix_analytics.py:19: new_code_2 = """        payload_obj = raw_payload if hasattr(raw_payload, "productId") else AnalyticsEventPayload(**(raw_payload.model_dump(exclude_unset=True) if hasattr(raw_payload, 'model_dump') else (raw_payload.root if hasattr(raw_payload, "root") else (raw_payload if isinstance(raw_payload, dict) else {}))))"""
fix_coupons.py:26: if hasattr(update_data, "minPurchaseAmount") and getattr(update_data, "minPurchaseAmount", None) is not None:
fix_coupons.py:29: if hasattr(update_data, "usageLimit") and getattr(update_data, "usageLimit", None) is not None:
fix_coupons.py:32: if hasattr(update_data, f):
fix_coupons_router.py:10: if hasattr(coupon_data, f):
fix_daos3.py:4: c = re.sub(r'merged = \w+InternalUpdate\(\**\{\**existing\.model_dump\(by_alias=True\), \**data\.model_dump\(exclude_unset=True\)\}\)', 'merged = {**existing.model_dump(by_alias=True), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)}', c)
fix_display_image.py:30: bundle_dict = bundle.model_dump() if hasattr(bundle, 'model_dump') else (bundle if isinstance(bundle, dict) else {})
fix_getattr.py:9: new_text = text.replace('getattr(d, "_id", getattr(d, "id", None))', 'd.id if hasattr(d, "id") else None')
fix_orders_dict.py:10: oid = str(p.orderId) if hasattr(p, "orderId") else str(p.order_id)
fix_orders_dict.py:20: oid = str(p.orderId) if hasattr(p, "orderId") else str(getattr(p, "order_id", getattr(p, "orderId", None)))
fix_remaining.py:7: text = text.replace("getattr(slot, 'configId', None)", "slot.configId if hasattr(slot, 'configId') else None")
fix_remaining.py:8: text = text.replace("slot.configId if hasattr(slot, 'configId') else None", "slot.configId")
fix_tests.py:9: content = content.replace('product["_id"]', 'product.id if hasattr(product, "id") else product["_id"]')
fix_tests.py:10: content = content.replace('product["id"]', 'product.id if hasattr(product, "id") else product["id"]')
fix_tests_bugs.py:41: c = c.replace('doc = {k: v for k, v in settings[0].items()}', 'doc = {k: v for k, v in settings[0].model_dump().items()} if hasattr(settings[0], "model_dump") else {k: v for k, v in settings[0].items()}')
fix_user_create.py:11: if "role" in user_data and hasattr(user_data["role"], "value"):
patch_stock_dao.py:15: res = res.replace('if "expiresAt" in data:', 'if (isinstance(data, dict) and "expiresAt" in data) or hasattr(data, "expiresAt"):')
.agents\auditor_m5\deep_attribute_checker.py:94: or hasattr(cls, attr)
backend\check_tables_v3.py:18: if isinstance(obj, type) and hasattr(obj, "model_fields") and name != "BaseModel":
backend\fix_base_dao.py:42: out.append('                    if hasattr(self, "clob_map") and k in self.clob_map:\n')
backend\fix_getattr_globally.py:6: r'existing_dict = existing if isinstance\(existing, dict\) else getattr\(existing, \"__dict__\", \{\}\)': r'existing_dict = existing.__dict__ if hasattr(existing, "__dict__") else {}',
backend\fix_tracking_dao.py:6: # Replace if hasattr(data, "...") and data... with if getattr(data, "...") if we don't know the type, but NO getattr allowed!
backend\fix_tracking_dao.py:46: # add_col("type", "event_type", data.type if hasattr(data, "type") else None)
backend\generate_daos.py:165: code.append('        if hasattr(r, "created_at") and r.created_at: out["createdAt"] = r.created_at.isoformat()')
backend\generate_daos.py:166: code.append('        if hasattr(r, "updated_at") and r.updated_at: out["updatedAt"] = r.updated_at.isoformat()')
backend\rewrite_orders.py:71: if hasattr(order_data, "referralCode") and order_data.referralCode:
backend\scratch_fix_dao2.py:15: if hasattr(data, "source") and data.source is not None: add_col("source", "source", data.source)
backend\scratch_fix_dao2.py:16: if hasattr(data, "filterType") and data.filterType is not None: add_col("filterType", "filter_type", data.filterType)
backend\scratch_fix_dao2.py:17: if hasattr(data, "filterValue") and data.filterValue is not None: add_col("filterValue", "filter_value", data.filterValue)
backend\scratch_fix_dao2.py:18: if hasattr(data, "campaign") and data.campaign is not None: add_col("campaign", "campaign", data.campaign)
backend\scratch_fix_dao2.py:19: if hasattr(data, "os") and data.os is not None: add_col("os", "os", data.os)
backend\scratch_fix_dao2.py:20: if hasattr(data, "browser") and data.browser is not None: add_col("browser", "browser", data.browser)
backend\scratch_fix_dao2.py:21: if hasattr(data, "ipAddress") and data.ipAddress is not None: add_col("ipAddress", "ip_address", data.ipAddress)'''
backend\scratch_fix_dao_row.py:16: timestamp=r.event_timestamp.isoformat() if hasattr(r.event_timestamp, "isoformat") else str(r.event_timestamp) if r.event_timestamp else None,
backend\scratch_fix_gets2.py:6: '''cat_dict["gst"] = (cat.gst if hasattr(cat, 'gst') and cat.gst is not None else 0) if not isinstance(cat, dict) else (cat.get("gst", 0))''',
backend\scratch_fix_session.py:7: '''existing_dict = existing.model_dump(exclude_unset=True) if hasattr(existing, 'model_dump') else dict(existing)''',
backend\scratch_fix_session.py:8: '''existing_dict = existing.model_dump(exclude_unset=True, by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)'''
backend\scratch_fix_test.py:11: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test.py:13: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_fix_test2.py:11: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test2.py:13: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_fix_test_again.py:8: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test_again.py:10: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_patch_auth_dump.py:8: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_categories_responses.py:8: c = c.replace('return result', 'return result.model_dump(by_alias=True, mode="json") if hasattr(result, "model_dump") else result')
backend\scratch_patch_categories_responses.py:9: c = c.replace('return created', 'return created.model_dump(by_alias=True, mode="json") if hasattr(created, "model_dump") else created')
backend\scratch_patch_categories_responses.py:10: c = c.replace('return updated', 'return updated.model_dump(by_alias=True, mode="json") if hasattr(updated, "model_dump") else updated')
backend\scratch_patch_categories_responses.py:11: c = c.replace('return category', 'return category.model_dump(by_alias=True, mode="json") if hasattr(category, "model_dump") else category')
backend\scratch_patch_daos.py:11: r'{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else dict(existing)), **\1}',
backend\scratch_patch_dict_compatible.py:12: if not hasattr(self, attr_name):
backend\scratch_patch_dict_compatible.py:21: return hasattr(self, self._get_alias_map().get(key, key))
backend\scratch_patch_orders.py:14: '{item.seller_id for item in order_items if hasattr(item, "seller_id") and item.seller_id}',
backend\scratch_patch_product_repo.py:8: 'cat_gst_map = {(cat.name if hasattr(cat, "name") else cat.get("name")): (cat.gst if hasattr(cat, "gst") else cat.get("gst", 0)) for cat in categories}'
backend\scratch_patch_routers_dump.py:18: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_routers_dump_safe.py:18: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_slots_dict.py:40: c = c.replace('slot.get("dict")()', 'slot.model_dump() if hasattr(slot, "model_dump") else slot.dict() if hasattr(slot, "dict") else slot')
backend\scratch_patch_update_session.py:10: existing_dict = existing.model_dump(by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)
backend\scratch_patch_valet_availability_dates.py:8: c = c.replace('return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.isoformat() if hasattr(doc.date, "isoformat") else doc.date) in upcoming_dates]', 'return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.strftime("%Y-%m-%d") if hasattr(doc.date, "strftime") else str(doc.date)[:10]) in upcoming_dates]')
backend\scratch_patch_valet_availability_responses.py:7: c = c.replace('return created', 'return created.model_dump(by_alias=True, mode="json") if hasattr(created, "model_dump") else created')
backend\scratch_patch_valet_availability_responses.py:8: c = c.replace('return [doc for doc in all_docs if doc.date in upcoming_dates]', 'return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.isoformat() if hasattr(doc.date, "isoformat") else doc.date) in upcoming_dates]')
backend\scratch_patch_valet_availability_responses.py:9: c = c.replace('return enriched', 'return [(e.model_dump(by_alias=True, mode="json") if hasattr(e, "model_dump") else e) for e in enriched] if enriched and hasattr(enriched[0], "model_dump") else enriched')
backend\scratch_tracking.py:166: name = v.productName if hasattr(v, "productName") else "Unknown"
backend\scratch_tracking.py:192: reason = d.reason if hasattr(d, "reason") else None
backend\app\db\mysql_flat_daos.py:1119: if hasattr(data, k) and getattr(data, k) is not None:
backend\app\db\mysql_generated_daos.py:183: if hasattr(data, api_k) and getattr(data, api_k) is not None:
backend\scratch\clean_all.py:8: # Pattern: **(user if hasattr(user, 'model_dump') else user)
backend\scratch\clean_all.py:12: # Pattern: X.Y if hasattr(X, "Y") else X.Z
backend\scratch\clean_all.py:19: # Pattern: X.Y if hasattr(X, "Y") else ( X["Y"] ... )
backend\scratch\clean_all.py:33: # if hasattr(X, "Y"): -> if X.Y:
backend\scratch\clean_all.py:34: content = re.sub(r'hasattr\(([^,]+),\s*\"([^\"]+)\"\)', r'hasattr(\1, "\2")', content) # wait, we can't do this globally easily, some might be used as boolean.
backend\scratch\clean_all.py:35: # Actually `hasattr(X, "Y")` -> `True` if it's a Pydantic model and we know it exists.
backend\scratch\clean_hasattr.py:8: # Pattern: X.Y if hasattr(X, "Y") else ( X["Y"] ... ) -> X.Y
backend\scratch\clean_hasattr.py:11: # Pattern: hasattr(X, "Y") -> True
backend\scratch\clean_hasattr.py:15: # `X = Y.Z if hasattr(Y, "Z") else ...`
backend\scratch\clean_hasattr.py:16: # Replace `Y.Z if hasattr(Y, "Z") else (...)` with `Y.Z`
backend\scratch\clean_hasattr.py:20: # We can just match hasattr(\w+, "\w+") and remove it. But wait, what if it's `if hasattr(user_val, "id"):`?
backend\scratch\clean_hasattr.py:23: # Let's replace `if hasattr(X, "Y"):` with `if True:` or remove the check if it's part of a generator.
backend\scratch\clean_hasattr.py:24: # Actually, `X.Y if hasattr(X, "Y") else None` is safe to replace with `X.Y`.
backend\scratch\clean_hasattr_final.py:16: content = content.replace('request.subscription.endpoint if hasattr(request.subscription, "endpoint") else (', 'request.subscription.endpoint if request.subscription.endpoint else (')
backend\scratch\clean_hasattr_final.py:17: content = content.replace('sub_payload = request.subscription.model_dump() if (has_web_subscription and hasattr(request.subscription, "model_dump")) else (request.subscription if has_web_subscription else None)', 'sub_payload = request.subscription.model_dump() if has_web_subscription else None')
backend\scratch\clean_hasattr_final.py:18: content = content.replace('p.images[0] if hasattr(p, "images") and p.images else (', 'p.images[0] if p.images else (')
backend\scratch\clean_hasattr_final.py:19: content = content.replace('if hasattr(order_data, "couponCode") and order_data.couponCode:', 'if getattr(order_data, "couponCode", None):')
backend\scratch\clean_hasattr_final.py:20: content = content.replace('if hasattr(order_data, "referralCode") and order_data.referralCode:', 'if getattr(order_data, "referralCode", None):')
backend\scratch\clean_hasattr_final.py:21: content = content.replace('elif hasattr(prod, "id"):', 'elif getattr(prod, "id", None):')
backend\scratch\clean_hasattr_final.py:22: content = content.replace('total = await user_repository.count(query) if hasattr(user_repository, "count") else len(users)', 'total = await user_repository.count(query)')
backend\scratch\clean_hasattr_final.py:23: content = content.replace('if hasattr(av_id, "id"):', 'if getattr(av_id, "id", None):')
backend\scratch\clean_hasattr_final.py:24: content = content.replace('if hasattr(perms, "serviceableZoneIds"):', 'if getattr(perms, "serviceableZoneIds", None):')
backend\scratch\clean_hasattr_final.py:25: content = content.replace('doc.date.strftime("%Y-%m-%d") if hasattr(doc.date, "strftime") else str(doc.date)[:10]', 'doc.date.strftime("%Y-%m-%d")')
backend\scratch\clean_hasattr_final.py:26: content = content.replace('item.product.id if hasattr(item.product, "id") else item.product', 'item.product.id')
backend\scratch\clean_hasattr_final.py:27: content = content.replace('[p.model_dump(by_alias=True) if hasattr(p, "model_dump") else p for p in payment_entries]', '[p.model_dump(by_alias=True) for p in payment_entries]')
backend\scratch\clean_hasattr_final.py:28: content = content.replace('product.model_dump(by_alias=True) if product and hasattr(product, "model_dump") else (product if product else {"_id": prod_id, "name": "Product not found"})', 'product.model_dump(by_alias=True) if product else {"_id": prod_id, "name": "Product not found"}')
backend\scratch\clean_hasattr_final.py:29: content = content.replace('[(e if hasattr(e, "model_dump") else e) for e in enriched] if enriched and hasattr(enriched[0], "model_dump") else enriched', '[e for e in enriched]')
backend\scratch\clean_orders.py:14: # Pattern: getattr(X, "Y", None) if hasattr(X, "Y") else (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
backend\scratch\code_check.py:9: 'hasattr()': [],
backend\scratch\code_check.py:43: if re_hasattr.search(line): violations['hasattr()'].append(f'{rel}:{i}')
backend\scratch\count_violations.py:9: "hasattr()": 0,
backend\scratch\count_violations.py:35: if re_hasattr.search(line): counts["hasattr()"] += 1
backend\scratch\count_violations2.py:9: "hasattr()": [],
backend\tests\test_catalog_routers_pydantic.py:31: assert hasattr(mod, 'router'), f'Router module {mod_name} must export a router'
backend\tests\test_coupon_mode.py:12: await product_repository.storage.delete(existing_product.id if hasattr(product, "id") else product["_id"])
backend\tests\test_coupon_mode.py:31: product_id = str(product.id if hasattr(product, "id") else product["_id"])
backend\tests\test_coupon_mode.py:133: await product_repository.storage.delete(product.id if hasattr(product, "id") else product["_id"])
backend\tests\test_orders_optimization.py:65: "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 2, "price": 100.0}],
backend\tests\test_orders_optimization.py:122: "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
backend\tests\test_orders_optimization.py:135: "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
backend\tests\test_orders_optimization.py:148: "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
backend\tests\test_overall_optimization.py:98: await wishlist_repository.addItem(user["_id"], {"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1})
backend\tests\test_overall_optimization.py:101: await cart_repository.addItem(user["_id"], {"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 2, "sellAsCase": False})
backend\tests\test_products_filtering.py:36: product_id = product.id if hasattr(product, "id") else product["_id"]
backend\tests\test_referrals.py:179: if pid and str(pid) == str(existing_product.id if hasattr(product, "id") else product["_id"]):
backend\tests\test_referrals.py:182: await product_repository.storage.delete(existing_product.id if hasattr(product, "id") else product["_id"])
backend\tests\test_referrals.py:196: "items": [{"productId": str(product.id if hasattr(product, "id") else product["_id"]), "quantity": 1}],
backend\tests\test_referrals.py:218: await product_repository.storage.delete(product.id if hasattr(product, "id") else product["_id"])
backend\tests\test_reviews_notifications.py:34: product_id = product.id if hasattr(product, "id") else product["_id"]
backend\tests\test_reviews_notifications.py:71: product_id = product.id if hasattr(product, "id") else product["_id"]
backend\tests\test_reviews_notifications.py:94: product_id = product.id if hasattr(product, "id") else product["_id"]
backend\tests\test_router_pydantic_refactor.py:282: if hasattr(r, "path"):
backend\tests\test_router_pydantic_refactor.py:284: elif hasattr(r, "include_context") and hasattr(r.include_context, "prefix"):
`

## getattr (466 hits)
`
clean_bundle_dicts.py:20: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))',
clean_bundle_dicts.py:21: 'sales_c = getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))'
clean_orders.py:9: new_users = 'users_map = {str(u.id): u for u in users_list if getattr(u, "id", None)}'
clean_orders.py:14: new_products = 'products_map = {str(p.id): p for p in products_list if getattr(p, "id", None)}'
clean_orders.py:22: oid = str(p.orderId) if hasattr(p, "orderId") else str(getattr(p, "order_id", getattr(p, "orderId", None)))
clean_orders.py:27: oid = str(getattr(p, "orderId", getattr(p, "order_id", None)))
clean_order_repo.py:9: content = re.sub(r'\(update_data\.get\("([a-zA-Z0-9_]+)"\)\s*if\s*isinstance\(update_data,\s*dict\)\s*else\s*getattr\(update_data,\s*"([a-zA-Z0-9_]+)",\s*None\)\)', r'getattr(update_data, "\2", None)', content)
clean_payment_repo.py:9: # replace (p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None)) with getattr(p, "paymentId", getattr(p, "payment_id", None))
clean_payment_repo.py:12: content = re.sub(pattern1, 'getattr(p, "paymentId", getattr(p, "payment_id", None))', content)
debug_coupons11.py:5: print("Table suffix:", getattr(settings, "table_suffix", ""))
fix_ad.py:80: if hasattr(data, api_k) and getattr(data, api_k) is not None:
fix_ad.py:82: params[api_k] = getattr(data, api_k)
fix_ad.py:91: if hasattr(data.stats, api_k) and getattr(data.stats, api_k) is not None:
fix_ad.py:93: params[f"st_{api_k}"] = getattr(data.stats, api_k)
fix_all.py:33: "pendingValetId": getattr(r, "pending_valet_id", None),
fix_all.py:34: "valetAssignedAt": r.valet_assigned_at.isoformat() + "Z" if getattr(r, "valet_assigned_at", None) else None,
fix_all.py:35: "valetCascadeCount": getattr(r, "valet_cascade_count", 0),
fix_all.py:36: "valetDeclineHistory": json_loads(r.valet_decline_history) if getattr(r, "valet_decline_history", None) else [],'''
fix_cat_dao.py:8: subCategories=update_data.subCategories if update_data.subCategories is not None else getattr(existing, 'subCategories', getattr(existing, 'sub_categories', [])),
fix_cat_dao.py:9: categoryTags=update_data.categoryTags if update_data.categoryTags is not None else getattr(existing, 'categoryTags', getattr(existing, 'category_tags', []))
fix_coupons.py:8: if getattr(update_data, "code", None):
fix_coupons.py:13: if getattr(update_data, "method", None) == "automatic":
fix_coupons.py:22: qt = getattr(update_data, "quantityTiers", None)
fix_coupons.py:26: if hasattr(update_data, "minPurchaseAmount") and getattr(update_data, "minPurchaseAmount", None) is not None:
fix_coupons.py:29: if hasattr(update_data, "usageLimit") and getattr(update_data, "usageLimit", None) is not None:
fix_coupons.py:33: v = getattr(update_data, f)
fix_coupons_router.py:11: kwargs[f] = getattr(coupon_data, f)
fix_cust.py:10: 'if ("_id" not in data if isinstance(data, dict) else not getattr(data, "id", None)):\n            if isinstance(data, dict):\n                data["_id"] = str(uuid.uuid4())\n            else:\n                data.id = str(uuid.uuid4())',
fix_daos.py:9: if 'getattr(d, "_id", getattr(d, "id", None))' in text:
fix_daos.py:10: text = text.replace('getattr(d, "_id", getattr(d, "id", None))', 'd.id')
fix_delivery.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n        for slot in slots:',
fix_delivery_slots_ast.py:9: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])',
fix_delivery_slots_ast.py:10: 'slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])'
fix_delivery_slot_clean.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n    for slot in slots:',
fix_delivery_slot_regex.py:11: r'\1slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n\1for slot in slots:',
fix_del_charges.py:7: content = content.replace('charge = (result.charge) or 0.0', 'charge = (result["charge"] if isinstance(result, dict) and "charge" in result else (getattr(result, "charge", None) if not isinstance(result, dict) else None)) or 0.0')
fix_del_slots.py:11: return f'slot["{prop}"] if isinstance(slot, dict) and "{prop}" in slot else getattr(slot, "{prop}", None)'
fix_del_slots_all.py:11: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_all.py:19: return getattr(s, p, None)
fix_del_slots_clean.py:10: return s[p] if isinstance(s, dict) and p in s else (getattr(s, p, None) if not isinstance(s, dict) else None)
fix_del_slots_clean.py:25: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_manual.py:11: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_manual.py:16: content = content.replace('slot.isActive', '(slot["isActive"] if isinstance(slot, dict) and "isActive" in slot else (getattr(slot, "isActive", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:17: content = content.replace('slot.isFullDay', '(slot["isFullDay"] if isinstance(slot, dict) and "isFullDay" in slot else (getattr(slot, "isFullDay", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:18: content = content.replace('slot.isUrgent', '(slot["isUrgent"] if isinstance(slot, dict) and "isUrgent" in slot else (getattr(slot, "isUrgent", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:19: content = content.replace('slot.startTime', '(slot["startTime"] if isinstance(slot, dict) and "startTime" in slot else (getattr(slot, "startTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:20: content = content.replace('slot.endTime', '(slot["endTime"] if isinstance(slot, dict) and "endTime" in slot else (getattr(slot, "endTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:21: content = content.replace('slot.cutoffTime', '(slot["cutoffTime"] if isinstance(slot, dict) and "cutoffTime" in slot else (getattr(slot, "cutoffTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:24: content = content.replace('cap_val = slot.capacity', 'cap_val = (slot["capacity"] if isinstance(slot, dict) and "capacity" in slot else (getattr(slot, "capacity", None) if not isinstance(slot, dict) else None))')
fix_display_image.py:17: getattr(bundle, "displayImage", getattr(bundle, "display_image", getattr(bundle, "imageUrl", getattr(bundle, "image_url", None))))
fix_generate_delete_many.py:6: text = text.replace('d_id = getattr(d, "_id", getattr(d, "id", None))', 'd_id = d.id')
fix_get.py:12: # qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)
fix_get.py:13: content = content.replace('item.get("quantity", getattr(item, "quantity", 1))', 'item["quantity"] if "quantity" in item else getattr(item, "quantity", 1)')
fix_getattr.py:9: new_text = text.replace('getattr(d, "_id", getattr(d, "id", None))', 'd.id if hasattr(d, "id") else None')
fix_getattr.py:11: new_text = text.replace('d_id = getattr(d, "_id", getattr(d, "id", None))', 'd_id = d.id')
fix_indent2.py:7: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n        product = await product_repository.findById(p_id)',
fix_indent2.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_indent2.py:11: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)',
fix_indent2.py:12: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_indent_flat_base.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_indent_order.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_indent_user.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_opt_tests.py:8: content = re.sub(r'u\.get\("email"\)', 'getattr(u, "email", None)', content)
fix_opt_tests.py:9: content = re.sub(r'u\.get\("name"\)', 'getattr(u, "name", None)', content)
fix_opt_tests.py:10: content = re.sub(r'u\["_id"\]', 'getattr(u, "id", getattr(u, "_id", None))', content)
fix_opt_tests.py:11: content = re.sub(r'p\.get\("name"\)', 'getattr(p, "name", None)', content)
fix_opt_tests.py:12: content = re.sub(r'p\.get\("sku"\)', 'getattr(p, "sku", None)', content)
fix_opt_tests.py:13: content = re.sub(r'p\["_id"\]', 'getattr(p, "id", getattr(p, "_id", None))', content)
fix_opt_tests.py:14: content = re.sub(r'res\["_id"\]', 'getattr(res, "id", getattr(res, "_id", None))', content)
fix_orders_dict.py:20: oid = str(p.orderId) if hasattr(p, "orderId") else str(getattr(p, "order_id", getattr(p, "orderId", None)))
fix_orders_populate.py:39: return getattr(obj, k, getattr(obj, k2, default))
fix_orders_populate_pydantic.py:23: couponCode=getattr(order_resp, "couponCode", None),
fix_orders_populate_pydantic.py:29: zoneId=getattr(order_resp, "zoneId", None),
fix_orders_populate_pydantic.py:31: adminNotes=getattr(order_resp, "adminNotes", None),
fix_orders_populate_pydantic.py:32: valetNotes=getattr(order_resp, "valetNotes", None)
fix_order_dao.py:15: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_ord_cleanup.py:8: content = re.sub(r'o\.get\("notes", ""\)', 'getattr(o, "notes", "") or ""', content)
fix_ord_cleanup.py:9: content = re.sub(r'o\["_id"\]', 'getattr(o, "id", getattr(o, "_id", None))', content)
fix_ord_cleanup.py:10: content = re.sub(r'p\.get\("customerName"\)', 'getattr(p, "customer_name", getattr(p, "customerName", None))', content)
fix_payment_dao_update.py:8: content = content.replace('val = existing[k] if k in existing else None', 'val = getattr(existing, k, None) if k != "orderId" else getattr(existing, "order_id", None) or getattr(existing, "orderId", None)')
fix_payment_repo3.py:15: entry_index = next((i for i, e in enumerate(entries) if (getattr(e, "entry_id", None) == str(entry_id) or getattr(e, "entry_id", None) == entry_id)), None)
fix_payment_repo_snake_case.py:8: content = content.replace('getattr(payment, "orderDate", None)', 'payment.order_date')
fix_payment_repo_snake_case.py:9: content = content.replace('getattr(payment, "createdAt", "")', 'payment.created_at or ""')
fix_remaining.py:7: text = text.replace("getattr(slot, 'configId', None)", "slot.configId if hasattr(slot, 'configId') else None")
fix_remaining.py:15: text = text.replace('getattr(doc, "displayId", None) if getattr(doc, "displayId", None) is not None', 'doc.displayId if doc.displayId is not None')
fix_remaining.py:16: text = text.replace('getattr(doc, "displayId", None)', 'doc.displayId')
fix_remaining.py:17: text = text.replace('getattr(coupon_data, "usageLimit", None)', 'coupon_data.usageLimit')
fix_remaining.py:18: text = text.replace('getattr(c, "displayId", None)', 'c.displayId')
fix_remaining.py:25: text = text.replace("getattr(subscription, 'endpoint', None)", "subscription.endpoint")
fix_remaining.py:26: text = text.replace("getattr(subscription, 'keys', {})", "(subscription.keys if subscription.keys is not None else {})")
fix_remaining.py:33: text = text.replace("getattr(segment, 'userIds', [])", "(segment.userIds if segment.userIds is not None else [])")
fix_remaining.py:40: text = text.replace('getattr(zone_doc, "defaultCapacity", 10)', '(zone_doc.defaultCapacity if zone_doc.defaultCapacity is not None else 10)')
fix_repo.py:4: 'variants=getattr(product_data, "variants", []),\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n',
fix_repo.py:5: 'variants=getattr(product_data, "variants", []),\n            variantAttributes=getattr(product_data, "variantAttributes", []),\n'
fix_segment.py:23: if (isinstance(data, dict) and data.get(k) is not None) or (not isinstance(data, dict) and getattr(data, k, None) is not None):
fix_segment.py:24: filters[k] = data.pop(k) if isinstance(data, dict) else getattr(data, k)
fix_sort2.py:8: new_code = 'enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else x.get("sales_count", 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)'
fix_sort2.py:9: new_code2 = 'enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else (x["sales_count"] if "sales_count" in x else 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)'
fix_tests_bugs.py:6: c = c.replace('res.get("userId")', 'getattr(res, "userId", getattr(res, "user_id", None))')
fix_user.py:8: content = content.replace('if update_data.email is not None:', 'email_val = update_data.get("email") if isinstance(update_data, dict) else getattr(update_data, "email", None)\n        if email_val is not None:')
fix_user.py:16: content = content.replace('otp_val = payload.otp', 'otp_val = payload.get("otp") if isinstance(payload, dict) else getattr(payload, "otp", None)')
fix_user_dao2.py:21: return getattr(obj, prop, default)
fix_user_dao2.py:23: payment_terms = _g(update_data, "payment_terms", getattr(update_data, "paymentTerms", existing.payment_terms))
fix_user_dao2.py:26: credit_limit = _g(update_data, "credit_limit", getattr(update_data, "creditLimit", existing.credit_limit))
fix_user_dao2.py:29: credit_used = _g(update_data, "credit_used", getattr(update_data, "creditUsed", existing.credit_used))
fix_user_dao2.py:32: approval_status = _g(update_data, "approval_status", getattr(update_data, "approvalStatus", existing.approval_status))
fix_user_dao3.py:14: content = content.replace("update_data.paymentTerms", "(update_data.get('paymentTerms', update_data.get('payment_terms')) if isinstance(update_data, dict) else getattr(update_data, 'payment_terms', getattr(update_data, 'paymentTerms', None)))")
fix_user_dao3.py:15: content = content.replace("update_data.creditLimit", "(update_data.get('creditLimit', update_data.get('credit_limit')) if isinstance(update_data, dict) else getattr(update_data, 'credit_limit', getattr(update_data, 'creditLimit', None)))")
fix_user_dao3.py:16: content = content.replace("update_data.creditUsed", "(update_data.get('creditUsed', update_data.get('credit_used')) if isinstance(update_data, dict) else getattr(update_data, 'credit_used', getattr(update_data, 'creditUsed', None)))")
fix_user_dao3.py:17: content = content.replace("update_data.approvalStatus", "(update_data.get('approvalStatus', update_data.get('approval_status')) if isinstance(update_data, dict) else getattr(update_data, 'approval_status', getattr(update_data, 'approvalStatus', None)))")
fix_user_dao4.py:8: content = content.replace("update_data.assignedSalesperson", "(update_data.get('assignedSalesperson', update_data.get('assigned_salesperson')) if isinstance(update_data, dict) else getattr(update_data, 'assigned_salesperson', getattr(update_data, 'assignedSalesperson', None)))")
fix_user_dao_final.py:27: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_user_dao_final2.py:8: # Instead of existing.prop, we use getattr(existing, 'prop', None)
fix_user_dao_final2.py:9: content = re.sub(r'existing\.([a-zA-Z_]+)', r"getattr(existing, '\1', None)", content)
fix_user_dao_getattr.py:8: # Replace all getattr(update_data, "field", getattr(existing, "field", None))
fix_user_repo_update2.py:7: content = content.replace('if update_data.password is not None:', 'if getattr(update_data, "password", getattr(update_data, "get", lambda x: None)("password")) is not None:')
fix_user_update.py:17: name = getattr(update_data, "name", existing.get("name"))
fix_user_update.py:18: email = getattr(update_data, "email", existing.get("email"))
fix_user_update.py:19: password_hash = getattr(update_data, "password", existing.get("password_hash"))
fix_user_update.py:20: role = getattr(update_data, "role", existing.get("role"))
fix_user_update.py:21: phone = getattr(update_data, "phone", existing.get("phone"))
fix_user_update.py:22: company_name = getattr(update_data, "companyName", existing.get("companyName"))
fix_user_update.py:23: is_active = getattr(update_data, "isActive", existing.get("isActive"))
fix_user_update.py:24: approval_status = getattr(update_data, "approvalStatus", existing.get("approvalStatus"))
fix_user_update.py:25: is_deactivated = getattr(update_data, "isDeactivated", existing.get("isDeactivated"))
fix_user_update.py:26: credit_limit = getattr(update_data, "creditLimit", existing.get("creditLimit"))
fix_user_update.py:27: credit_used = getattr(update_data, "creditUsed", existing.get("creditUsed"))
fix_user_update.py:28: payment_terms = getattr(update_data, "paymentTerms", existing.get("paymentTerms"))
fix_user_update.py:29: assigned_salesperson = getattr(update_data, "assignedSalesperson", existing.get("assignedSalesperson"))
fix_user_update.py:30: is_email_verified = getattr(update_data, "isEmailVerified", existing.get("isEmailVerified"))
fix_user_update.py:31: referral_code = getattr(update_data, "referralCode", existing.get("referralCode"))
fix_user_update.py:32: is_seller_admin = getattr(update_data, "isSellerAdmin", existing.get("isSellerAdmin"))
fix_user_update.py:33: is_on_duty = getattr(update_data, "isOnDuty", existing.get("isOnDuty"))
fix_user_update.py:34: commission_override_pct = getattr(update_data, "commissionOverridePct", existing.get("commissionOverridePct"))
fix_user_update.py:35: upi_id = getattr(update_data, "upiId", existing.get("upiId"))
fix_user_update.py:36: qr_code_url = getattr(update_data, "qrCodeUrl", existing.get("qrCodeUrl"))
fix_user_update_again.py:7: # Replace existing.get with getattr(existing, ...)
fix_user_update_again.py:8: content = content.replace('existing.get("name")', 'getattr(existing, "name", None)')
fix_user_update_again.py:9: content = content.replace('existing.get("email")', 'getattr(existing, "email", None)')
fix_user_update_again.py:10: content = content.replace('existing.get("password_hash")', 'getattr(existing, "password", None)')
fix_user_update_again.py:11: content = content.replace('existing.get("role")', 'getattr(existing, "role", None)')
fix_user_update_again.py:12: content = content.replace('existing.get("phone")', 'getattr(existing, "phone", None)')
fix_user_update_again.py:13: content = content.replace('existing.get("companyName")', 'getattr(existing, "companyName", None)')
fix_user_update_again.py:14: content = content.replace('existing.get("isActive")', 'getattr(existing, "isActive", None)')
fix_user_update_again.py:15: content = content.replace('existing.get("approvalStatus")', 'getattr(existing, "approvalStatus", None)')
fix_user_update_again.py:16: content = content.replace('existing.get("isDeactivated")', 'getattr(existing, "isDeactivated", None)')
fix_user_update_again.py:17: content = content.replace('existing.get("creditLimit")', 'getattr(existing, "creditLimit", None)')
fix_user_update_again.py:18: content = content.replace('existing.get("creditUsed")', 'getattr(existing, "creditUsed", None)')
fix_user_update_again.py:19: content = content.replace('existing.get("paymentTerms")', 'getattr(existing, "paymentTerms", None)')
fix_user_update_again.py:20: content = content.replace('existing.get("assignedSalesperson")', 'getattr(existing, "assignedSalesperson", None)')
fix_user_update_again.py:21: content = content.replace('existing.get("isEmailVerified")', 'getattr(existing, "isEmailVerified", None)')
fix_user_update_again.py:22: content = content.replace('existing.get("referralCode")', 'getattr(existing, "referralCode", None)')
fix_user_update_again.py:23: content = content.replace('existing.get("isSellerAdmin")', 'getattr(existing, "isSellerAdmin", None)')
fix_user_update_again.py:24: content = content.replace('existing.get("isOnDuty")', 'getattr(existing, "isOnDuty", None)')
fix_user_update_again.py:25: content = content.replace('existing.get("commissionOverridePct")', 'getattr(existing, "commissionOverridePct", None)')
fix_user_update_again.py:26: content = content.replace('existing.get("upiId")', 'getattr(existing, "upiId", None)')
fix_user_update_again.py:27: content = content.replace('existing.get("qrCodeUrl")', 'getattr(existing, "qrCodeUrl", None)')
patch_analytics_test.py:10: 'event_records = [r for r in all_event_records if r.payload and getattr(r.payload, "testRunId", None) == session_id]'
patch_bundles_router.py:8: 'getattr(bundle, "isActive", getattr(bundle, "is_active", None)) if getattr(bundle, "isActive", getattr(bundle, "is_active", None)) is not None'
patch_bundle_dao_cls.py:12: content = content.replace('(doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id")))', 'doc.external_id if getattr(doc, "external_id", None) is not None else doc.id')
patch_bundle_dao_id.py:7: 'doc.external_id if getattr(doc, "external_id", None) is not None else doc.id',
patch_bundle_dao_id_restore.py:6: content = content.replace('doc.id', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')
patch_bundle_dao_id_restore.py:8: content = content.replace('((doc.external_id if getattr(doc, "external_id", None) is not None else doc.id))', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')
patch_bundle_dao_id_restore.py:9: content = content.replace('(doc.external_id if getattr(doc, "external_id", None) is not None else (doc.external_id if getattr(doc, "external_id", None) is not None else doc.id))', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')
patch_bundle_repo.py:8: 'if any(getattr(i, "productId", i.get("productId", i.get("product_id")) if isinstance(i, dict) else getattr(i, "product_id", None)) == product_id for i in items):'
patch_flat_base.py:8: '''cls = getattr(self, "schema_cls", getattr(self, "pydantic_model", None))
patch_flat_base_dao.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_flat_base_dao.py:10: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", [])}
patch_flat_base_dao.py:14: 'existing_dict = existing if isinstance(existing, dict) else existing.__dict__\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_flat_base_dao2.py:8: replacement = '''existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_flat_base_dao2.py:12: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
patch_mysql_flat_base_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else existing.__dict__\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_mysql_order_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_mysql_user_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_orders.py:8: 'return getattr(product, "seller_id", None)'
patch_orders2.py:8: 'variantAttributes=getattr(item, "variantAttributes", getattr(item, "variant_attributes", None))'
patch_orders2.py:12: 'variantAttributes=getattr(item, "variantAttributes", getattr(item, "variant_attributes", None))'
patch_orders4.py:20: 'str(getattr(i, "product_id", getattr(i, "productId", ""))) == spec_pid'
patch_orders5.py:8: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))\n                    new_sales = (sales_c if sales_c is not None else 0) + copies'
patch_order_clean.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_order_clean.py:13: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
patch_order_dao_update2.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_order_dao_update2.py:10: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", [])}
patch_order_dao_update2.py:14: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_order_fields.py:8: '        if isinstance(update_data, dict):\n            return await self.storage.update(id, update_data)\n        fields = {}\n        for f in getattr(update_data, "model_fields_set", []):'
patch_order_repo_fixed.py:9: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_fixed.py:12: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_fixed.py:20: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_fixed.py:28: if order and getattr(order, "paymentMethod", None) == "cod":
patch_order_repo_fixed.py:29: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_order_repo_replace.py:16: '(update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)) is None'
patch_order_repo_replace.py:24: '(update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)) is None'
patch_order_repo_replace.py:32: '(update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)) is None'
patch_order_repo_replace.py:40: '(update_data.get("codPaymentReceived") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceived", None)) is None'
patch_order_repo_replace.py:48: '(update_data.get("codPaymentReceivedAt") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceivedAt", None)) is None'
patch_order_repo_replace.py:60: '(update_data.get("cancelledAt") if isinstance(update_data, dict) else getattr(update_data, "cancelledAt", None)) is None'
patch_order_repo_replace.py:69: 'datetime.fromisoformat((update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt"))'
patch_order_repo_rewrite.py:10: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_rewrite.py:13: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_rewrite.py:21: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_rewrite.py:29: if order and getattr(order, "paymentMethod", None) == "cod":
patch_order_repo_rewrite.py:30: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_payment.py:8: '(p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None))'
patch_prod_repo_vars.py:9: 'variants=product_data.variantCombinations if getattr(product_data, "variantCombinations", None) is not None else [],\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n'
patch_prod_repo_vars_fix.py:8: 'variants=product_data.variantCombinations if getattr(product_data, "variantCombinations", None) is not None else [],\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n',
patch_prod_repo_vars_fix.py:9: 'variants=getattr(product_data, "variants", []),\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n'
patch_prod_repo_vid.py:9: 'images=product_data.images if product_data.images is not None else [],\n            videos=getattr(product_data, "videos", []),'
patch_routers_bundles3.py:8: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)'
patch_routers_bundles_pid.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
patch_routers_bundles_pid.py:24: 'available < (item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1))'
patch_routers_bundles_pid.py:28: 'required: {item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)}'
patch_routers_bundles_pid.py:32: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))'
patch_routers_bundles_pid.py:36: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)'
patch_stock_dao.py:10: res = res.replace('data.productId', 'data.get("productId") if isinstance(data, dict) else getattr(data, "productId", None)')
patch_stock_dao.py:11: res = res.replace('data.userId', 'data.get("userId") if isinstance(data, dict) else getattr(data, "userId", None)')
patch_stock_dao.py:12: res = res.replace('data.quantity', 'data.get("quantity") if isinstance(data, dict) else getattr(data, "quantity", None)')
patch_stock_dao.py:13: res = res.replace('data.status', 'data.get("status") if isinstance(data, dict) else getattr(data, "status", None)')
patch_stock_dao.py:14: res = res.replace('data.expiresAt', 'data.get("expiresAt") if isinstance(data, dict) else getattr(data, "expiresAt", None)')
patch_stock_reservations_dao.py:14: data_dict = data if isinstance(data, dict) else getattr(data, '__dict__', {})
patch_user_careful.py:16: lines[i] = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_careful.py:20: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
patch_user_careful.py:27: line = line.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_careful.py:28: line = line.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_careful.py:48: lines[i] = '    async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n'
patch_user_children_both.py:12: # Insert data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})
patch_user_children_both.py:13: rep_block = rep_block.replace('async def _replace_children(self, session, uid: int, data: Dict):\n', 'async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n')
patch_user_clean.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_clean.py:13: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
patch_user_clean.py:22: # Fix getattr(merged, ...)
patch_user_clean.py:23: content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_clean.py:24: content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_dao_merged.py:13: # We also have getattr(merged, 'upiId', None) which is not valid on dict
patch_user_dao_merged.py:14: content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_dao_merged.py:15: content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_dao_update.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_dao_update.py:10: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", [])}
patch_user_dao_update.py:14: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_user_final.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_final.py:13: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
patch_user_final.py:26: update_block = update_block.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_final.py:27: update_block = update_block.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_zone.py:8: 'if pincode in (zone.get("pincodes", []) if isinstance(zone, dict) else (getattr(zone, "pincodes", []) or [])):'
repro_bundle.py:14: print("Success:", getattr(b, "id", "No ID"))
rewrite_brand_repo.py:8: name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_brand_repo.py:9: description=getattr(data, 'description', data.get('description') if isinstance(data, dict) else None),
rewrite_brand_repo.py:10: isActive=getattr(data, 'isActive', data.get('isActive') if isinstance(data, dict) else True)
rewrite_create.py:80: "delivery_slot_config_id": getattr(slot, 'configId', None) if slot else None,
rewrite_repos.py:60: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos2.py:50: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos2.py:80: replacement += f"                if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos3.py:49: mapping.append(f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos3.py:79: replacement += f"{indent}        if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos4.py:44: #                name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_repos4.py:75: #                if 'name' in data.model_fields_set: internal_data.name = getattr(data, 'name')
rewrite_repos_manual.py:28: res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos_manual.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_2.py:28: res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos_manual_2.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_3.py:28: res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos_manual_3.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_4.py:28: res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
rewrite_repos_manual_5.py:30: res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
.agents\auditor_m5\deep_attribute_checker.py:75: # Look up class in inline_models or SCHEMA_MODELS or getattr(mod, ann_str, None)
.agents\auditor_m5\deep_attribute_checker.py:76: cls = inline_models.get(ann_str) or SCHEMA_MODELS.get(ann_str) or getattr(mod, ann_str, None)
.agents\auditor_m5\deep_attribute_checker.py:95: or attr in getattr(cls, "__annotations__", {})
.agents\auditor_m5\deep_attribute_checker.py:99: has_alias = any(getattr(f, 'alias', None) == attr for f in cls.model_fields.values())
.agents\explorer_survey_2\dump_calls.py:27: "end": getattr(node, 'end_lineno', node.lineno),
backend\check_tables_v3.py:17: obj = getattr(schemas, name)
backend\fix_base_dao.py:7: if 'cls = getattr(self, "schema_cls", getattr(self, "pydantic_model", None))' in line:
backend\fix_base_dao_clean.py:6: # Fix the schema_cls getattr (Line 101 approx)
backend\fix_base_dao_clean.py:7: old_cls = 'cls = getattr(self, "schema_cls", getattr(self, "pydantic_model", None))'
backend\fix_base_dao_clean.py:26: update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
backend\fix_bundles.py:32: r'if not getattr(bundle, "isActive", True):',
backend\fix_bundles.py:35: content = content.replace('if not getattr(bundle, "isActive", True):', 'if not bundle.isActive:')
backend\fix_bundles.py:39: r'if not bundle or not getattr(bundle, "isActive", True):',
backend\fix_bundles.py:42: content = content.replace('if not bundle or not getattr(bundle, "isActive", True):', 'if not bundle or not bundle.isActive:')
backend\fix_bundles.py:47: r'if available < getattr(item, "quantity", 1):',
backend\fix_bundles.py:50: content = content.replace('if available < getattr(item, "quantity", 1):', 'if available < (item.quantity or 1):')
backend\fix_bundle_dao.py:6: content = content.replace('getattr(doc, "external_id", None)', 'doc.external_id')
backend\fix_getattr_globally.py:7: r'update_dict = \{k: getattr\(update_data, k\) for k in getattr\(update_data, \"model_fields_set\", getattr\(update_data, \"__dict__\", \{\}\)\)\}': r'update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}', # these are base daos, they need getattr since they operate on Any Model, wait no getattr!
backend\fix_minor_getattr.py:6: content = content.replace('getattr(update_data, "model_fields_set", [])', 'update_data.model_fields_set')
backend\fix_minor_getattr.py:14: content = content.replace('def get_prop(s, p):\n    return getattr(s, p, None)', 'def get_prop(s, p):\n    return getattr(s, p, None)')
backend\fix_mysql_order_dao.py:9: if 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})' in line:
backend\fix_mysql_user_dao.py:12: "        name = update_data.name if getattr(update_data, 'name', None) is not None else existing.name\n",
backend\fix_mysql_user_dao.py:13: "        email = update_data.email if getattr(update_data, 'email', None) is not None else existing.email\n",
backend\fix_mysql_user_dao.py:14: "        password_hash = update_data.password if getattr(update_data, 'password', None) is not None else existing.password\n",
backend\fix_mysql_user_dao.py:15: "        role = update_data.role if getattr(update_data, 'role', None) is not None else existing.role\n",
backend\fix_mysql_user_dao.py:16: "        phone = update_data.phone if getattr(update_data, 'phone', None) is not None else existing.phone\n",
backend\fix_mysql_user_dao.py:17: "        company_name = update_data.companyName if getattr(update_data, 'companyName', None) is not None else existing.company_name\n",
backend\fix_mysql_user_dao.py:18: "        gst_number = update_data.gstNumber if getattr(update_data, 'gstNumber', None) is not None else existing.gst_number\n",
backend\fix_mysql_user_dao.py:19: "        is_deactivated = update_data.isDeactivated if getattr(update_data, 'isDeactivated', None) is not None else existing.is_deactivated\n",
backend\fix_mysql_user_dao.py:20: "        credit_limit = update_data.creditLimit if getattr(update_data, 'creditLimit', None) is not None else existing.credit_limit\n",
backend\fix_mysql_user_dao.py:21: "        credit_used = update_data.creditUsed if getattr(update_data, 'creditUsed', None) is not None else existing.credit_used\n",
backend\fix_mysql_user_dao.py:22: "        payment_terms = update_data.paymentTerms if getattr(update_data, 'paymentTerms', None) is not None else existing.payment_terms\n",
backend\fix_mysql_user_dao.py:23: "        assigned_salesperson = update_data.assignedSalesperson if getattr(update_data, 'assignedSalesperson', None) is not None else existing.assigned_salesperson\n",
backend\fix_mysql_user_dao.py:24: "        is_email_verified = update_data.isEmailVerified if getattr(update_data, 'isEmailVerified', None) is not None else existing.is_email_verified\n",
backend\fix_mysql_user_dao.py:25: "        referral_code = update_data.referralCode if getattr(update_data, 'referralCode', None) is not None else existing.referral_code\n",
backend\fix_mysql_user_dao.py:26: "        is_seller_admin = update_data.isSellerAdmin if getattr(update_data, 'isSellerAdmin', None) is not None else existing.is_seller_admin\n",
backend\fix_mysql_user_dao.py:27: "        is_on_duty = update_data.isOnDuty if getattr(update_data, 'isOnDuty', None) is not None else existing.is_on_duty\n",
backend\fix_mysql_user_dao.py:28: "        commission_override_pct = update_data.commissionOverridePct if getattr(update_data, 'commissionOverridePct', None) is not None else existing.commission_override_pct\n",
backend\fix_mysql_user_dao.py:29: "        upi_id = update_data.upiId if getattr(update_data, 'upiId', None) is not None else existing.upi_id\n",
backend\fix_mysql_user_dao.py:30: "        qr_code_url = update_data.qrCodeUrl if getattr(update_data, 'qrCodeUrl', None) is not None else existing.qr_code_url\n"
backend\fix_mysql_user_dao_again.py:13: # fields_set = getattr(update_data, 'model_fields_set', getattr(update_data, '__fields_set__', set()))
backend\fix_mysql_user_dao_again.py:15: content = content.replace("getattr(update_data, 'model_fields_set', getattr(update_data, '__fields_set__', set()))", "update_data.model_fields_set")
backend\fix_remove_update_dict.py:9: if 'update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}' in line:
backend\fix_tracking_dao.py:6: # Replace if hasattr(data, "...") and data... with if getattr(data, "...") if we don't know the type, but NO getattr allowed!
backend\fix_tracking_dao.py:85: r'filter_type = data.filterName if getattr(data, "filterName", None) is not None else getattr(data, "filterType", get_payload_extra("filterType"))', # wait, NO getattr!
backend\generate_daos.py:157: code.append('        suffix = getattr(settings, "table_suffix", "")')
backend\generate_daos.py:164: code.append('        out = {"_id": str(r.id), "externalId": getattr(r, "external_id", None)}')
backend\generate_daos.py:169: code.append("            val = getattr(r, db_col, None)")
backend\generate_daos.py:204: code.append("                        c_map[row.parent_id][api_key].append(getattr(row, db_cols[0]))")
backend\generate_daos.py:206: code.append("                        k = getattr(row, db_cols[0])")
backend\generate_daos.py:207: code.append("                        v = getattr(row, db_cols[1])")
backend\generate_daos.py:212: code.append("                            obj[api_cols[i]] = getattr(row, db_c)")
backend\scratch_add_sellers_dao.py:16: for seller in (data.sellers if getattr(data, 'sellers', None) is not None else []):
backend\scratch_analytics_router.py:45: if getattr(event.payload, "testRunId", None) is not None:
backend\scratch_analytics_router.py:46: payload_items.append(EventPayloadItem(key="testRunId", value=str(getattr(event.payload, "testRunId"))))
backend\scratch_fix.py:10: lines[i] = '                item_date = self._parse_date(item.createdAt if getattr(item, "createdAt", None) else "")\n'
backend\scratch_fix.py:14: lines[i] = '                item_date = self._parse_date(item.timestamp if getattr(item, "timestamp", None) else "")\n'
backend\scratch_fix_all_gets.py:17: content = re.sub(var_regex + r'\.get\(([a-zA-Z0-9_]+),\s*([^)]+)\)', r'(getattr(\1, \2, \3) if getattr(\1, \2, None) is not None else \3)', content)
backend\scratch_fix_all_gets.py:19: # User said NO model_dump(), NO getattr()!
backend\scratch_fix_analytics_events.py:27: if getattr(event, "page", None):
backend\scratch_fix_date_filter.py:7: 'item_date = self._parse_date((getattr(item, date_field, "") if getattr(item, date_field, None) is not None else ""))',
backend\scratch_fix_gets.py:17: 'ticket.get("user_id") if isinstance(ticket, dict) else getattr(ticket, "user_id", None)',
backend\scratch_fix_gets.py:21: 'ticket.get("userId") if isinstance(ticket, dict) else getattr(ticket, "userId", None)',
backend\scratch_fix_gets.py:33: 'str(ticket.get("id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "id", ""))',
backend\scratch_fix_gets.py:37: 'str(ticket.get("_id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "_id", ""))',
backend\scratch_fix_slots_id.py:35: 'if getattr(sl, "id", None) == order_data.deliverySlotId or f"{getattr(sl, \'start_time\', \'\')}-{getattr(sl, \'end_time\', \'\')}" == order_data.deliverySlotId or getattr(sl, "get", lambda x: None)("id") == order_data.deliverySlotId:'
backend\scratch_fix_slots_id.py:42: 'if getattr(sl, "id", getattr(sl, "get", lambda x: None)("id")) == slot_id or f"{getattr(sl, \'start_time\', getattr(sl, \'get\', lambda x: \'\')(\'startTime\'))}-{getattr(sl, \'end_time\', getattr(sl, \'get\', lambda x: \'\')(\'endTime\'))}" == slot_id:'
backend\scratch_fix_slots_id.py:46: 'sl["bookedCount"] = (int(getattr(sl, "booked_count", getattr(sl, "get", lambda x: 0)("bookedCount"))) if getattr(sl, "booked_count", getattr(sl, "get", lambda x: 0)("bookedCount")) is not None else 0) + 1'
backend\scratch_patch_auth.py:5: c = c.replace('user["_id"]', 'getattr(user, "id", None)')
backend\scratch_patch_auth.py:6: c = c.replace('user["isDeactivated"]', 'getattr(user, "is_deactivated", False)')
backend\scratch_patch_auth.py:7: c = c.replace('user["approvalStatus"]', 'getattr(user, "approval_status", None)')
backend\scratch_patch_auth.py:8: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_auth.py:9: c = c.replace('user.get("role")', 'getattr(user, "role", None)')
backend\scratch_patch_auth.py:10: c = c.replace('user.get("isActive")', 'getattr(user, "is_active", True)')
backend\scratch_patch_auth.py:11: c = c.replace('user.get("isEmailVerified")', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_auth_revoked.py:5: c = c.replace('session.get("revokedAt")', 'getattr(session, "revoked_at", None)')
backend\scratch_patch_auth_revoked.py:6: c = c.replace('session.get("revokedReason")', 'getattr(session, "revoked_reason", None)')
backend\scratch_patch_auth_session.py:5: c = c.replace('session["_id"]', 'getattr(session, "id", None)')
backend\scratch_patch_auth_session.py:6: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_auth_session_dict.py:8: c = re.sub(r'session\.get\("userId"\)', 'getattr(session, "user_id", None)', c)
backend\scratch_patch_auth_session_dict.py:9: c = re.sub(r'session\.get\("isReturning"\)', 'getattr(session, "is_returning", None)', c)
backend\scratch_patch_auth_session_dict.py:10: c = re.sub(r'session\.get\("timestamp"\)', 'getattr(session, "timestamp", None)', c)
backend\scratch_patch_auth_user_dict.py:9: c = re.sub(r'user\.get\("role"\)', 'getattr(user, "role", None)', c)
backend\scratch_patch_auth_user_dict.py:10: c = re.sub(r'user\.get\("_id"\)', 'getattr(user, "id", None)', c)
backend\scratch_patch_dao_gets.py:6: c = c.replace('existing.get("_db_id")', 'getattr(existing, "_db_id", None)')
backend\scratch_patch_dao_gets.py:10: c = c.replace('doc.get("external_id")', 'getattr(doc, "external_id", getattr(doc, "id", None))')
backend\scratch_patch_dict_access.py:12: (r'user\["address"\]\.get', 'getattr(user, "address", {}).get'),
backend\scratch_patch_dict_access.py:16: (r'user\.get\("createdAt"\)', 'getattr(user, "created_at", None)'),
backend\scratch_patch_dict_access.py:17: (r'user\.get\("role"\)', 'getattr(user, "role", None)'),
backend\scratch_patch_dict_access.py:18: (r'user\.get\("_id"\)', 'getattr(user, "id", None)'),
backend\scratch_patch_dict_access.py:19: (r'user\.get\("name"\)', 'getattr(user, "name", None)'),
backend\scratch_patch_dict_access.py:20: (r'user\.get\("email"\)', 'getattr(user, "email", None)'),
backend\scratch_patch_dict_access.py:21: (r'user\.get\("address"\)', 'getattr(user, "address", {})'),
backend\scratch_patch_dict_access.py:22: (r'user\.get\("companyName"\)', 'getattr(user, "company_name", None)'),
backend\scratch_patch_dict_access.py:23: (r'user\.get\("customerId"\)', 'getattr(user, "user_id_formatted", None)'),
backend\scratch_patch_dict_access.py:25: (r'session\.get\("userId"\)', 'getattr(session, "user_id", None)'),
backend\scratch_patch_dict_access.py:26: (r'session\.get\("isReturning"\)', 'getattr(session, "is_returning", None)'),
backend\scratch_patch_dict_access.py:27: (r'session\.get\("timestamp"\)', 'getattr(session, "timestamp", None)'),
backend\scratch_patch_dict_access.py:29: (r'response_user\.get\("_id"\)', 'getattr(response_user, "id", None)'),
backend\scratch_patch_dict_access.py:30: (r'response_user\.get\("name"\)', 'getattr(response_user, "name", None)'),
backend\scratch_patch_dict_access.py:31: (r'response_user\.get\("email"\)', 'getattr(response_user, "email", None)'),
backend\scratch_patch_dict_access.py:32: (r'response_user\.get\("role"\)', 'getattr(response_user, "role", None)'),
backend\scratch_patch_dict_access.py:34: (r'existing_user\.get\("email"\)', 'getattr(existing_user, "email", None)'),
backend\scratch_patch_dict_access.py:35: (r'existing_user\.get\("companyName"\)', 'getattr(existing_user, "company_name", None)'),
backend\scratch_patch_dict_access.py:36: (r'existing_user\.get\("address"\)', 'getattr(existing_user, "address", {})'),
backend\scratch_patch_dict_access.py:37: (r'existing_user\.get\("role"\)', 'getattr(existing_user, "role", None)'),
backend\scratch_patch_dict_access.py:39: (r'v_user\.get\("role"\)', 'getattr(v_user, "role", None)'),
backend\scratch_patch_dict_compatible.py:8: return getattr(self, self._get_alias_map().get(key, key), default)
backend\scratch_patch_dict_compatible.py:14: return getattr(self, attr_name)
backend\scratch_patch_dict_logic.py:6: 'if getattr(user, "address", {}) and getattr(user, "address", {}) not in getattr(user, "saved_addresses", []):',
backend\scratch_patch_isActive.py:14: c = c.replace('user.get("isActive", True)', 'getattr(user, "is_active", True)')
backend\scratch_patch_isActive.py:15: c = c.replace('user.get("isEmailVerified", False)', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_isActive.py:20: c = c.replace('user.get("isActive", True)', 'getattr(user, "is_active", True)')
backend\scratch_patch_isActive.py:21: c = c.replace('user.get("isEmailVerified", False)', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_more.py:5: c = c.replace('user.get("effectiveRole")', 'getattr(user, "effectiveRole", None)')
backend\scratch_patch_more.py:12: c = c.replace('if user["address"] and user["address"] not in user["savedAddresses"]:', 'if getattr(user, "address", {}) and getattr(user, "address", {}) not in getattr(user, "saved_addresses", []):')
backend\scratch_patch_repo.py:5: c = c.replace('user.get("password")', 'getattr(user, "password", None)')
backend\scratch_patch_repo.py:6: c = c.replace('user.get("password", "")', 'getattr(user, "password", "")')
backend\scratch_patch_repo.py:7: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_repo.py:9: c = c.replace('user.get("referralCode")', 'getattr(user, "referral_code", None)')
backend\scratch_patch_repo2.py:5: c = c.replace('user.get("savedAddresses", [])', 'getattr(user, "saved_addresses", [])')
backend\scratch_patch_session_dict.py:5: c = c.replace('session.get("lastActiveAt")', 'getattr(session, "last_active_at", None)')
backend\scratch_patch_session_dict.py:7: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_session_dict.py:13: c = c.replace('session.get("status")', 'getattr(session, "status", None)')
backend\scratch_patch_session_dict.py:14: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_session_dict.py:15: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_session_dict.py:16: c = c.replace('user.get("isDeactivated")', 'getattr(user, "is_deactivated", False)')
backend\scratch_patch_session_dict.py:17: c = c.replace('user.get("role")', 'getattr(user, "role", None)')
backend\scratch_patch_users_variables.py:7: 'if not existing_user or getattr(user, "email", None) != new_email:',
backend\scratch_patch_users_variables.py:8: 'if not existing_user or getattr(existing_user, "email", None) != new_email:'
backend\scratch_patch_users_variables.py:11: 'else getattr(user, "company_name", None)',
backend\scratch_patch_users_variables.py:12: 'else getattr(existing_user, "company_name", None)'
backend\scratch_patch_users_variables.py:15: 'else getattr(user, "address", {})',
backend\scratch_patch_users_variables.py:16: 'else getattr(existing_user, "address", {})'
backend\scratch_patch_users_variables.py:19: 'getattr(user, "role", None) == "wholesaler":',
backend\scratch_patch_users_variables.py:20: 'getattr(existing_user, "role", None) == "wholesaler":'
backend\scratch_patch_users_variables.py:24: 'if existing_with_email and str(getattr(existing_with_email, "id", None) or getattr(existing_with_email, "_id", None)) != user_id:'
backend\scratch_patch_verify_token.py:17: if getattr(user, "is_deactivated", False) and getattr(user, "role", None) == "wholesaler":
backend\scratch_patch_verify_token.py:20: user.effective_role = getattr(user, "role", "customer")
backend\scratch_patch_verify_token.py:36: 'effective = getattr(user, "effectiveRole", None) or getattr(user, "role", None)',
backend\scratch_patch_verify_token.py:37: 'effective = getattr(user, "effective_role", None) or getattr(user, "role", None)'
backend\scratch_replace_get.py:24: return f"({obj_str}.{prop} if getattr({obj_str}, '{prop}', None) is not None else {default})"
backend\scratch_test_db_user.py:18: print("Role in Model:", getattr(user_model, "role", "NO_ROLE_ATTR"))
backend\scratch_test_db_user_2.py:12: email = getattr(u, "email", "") or ""
backend\scratch_test_db_user_2.py:13: if getattr(u, "role") == "super_admin" or email.startswith("admin_"):
backend\scratch_test_db_user_2.py:15: print("Role in Model:", getattr(u, "role", "NO_ROLE_ATTR"))
backend\scratch_test_db_user_2.py:16: print("Effective role:", getattr(u, "effectiveRole", "NO_EFF_ROLE_ATTR"))
backend\scratch_tracking.py:231: items = getattr(a, "cartItems", []) or []
backend\scratch_tracking.py:233: pid = getattr(item, "product", None) or getattr(item, "productId", None)
backend\scratch_tracking.py:245: q = getattr(item, "quantity", 1) or 1
backend\scratch_tracking.py:246: p = getattr(item, "price", 0) or 0
backend\scratch_tracking.py:321: term = (getattr(s, "searchTerm", "") or "").strip().lower()
backend\scratch_tracking.py:324: unique_searches.append(getattr(s, "searchTerm", ""))
backend\scratch_tracking.py:346: for pid in getattr(doc, "productIds", []) or []:
backend\scratch_tracking.py:359: pids = getattr(doc, "productIds", []) or []
backend\app\db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
backend\app\db\mysql_flat_daos.py:1119: if hasattr(data, k) and getattr(data, k) is not None:
backend\app\db\mysql_flat_daos.py:1120: kwargs[k] = getattr(data, k)
backend\app\db\mysql_flat_daos.py:1122: kwargs[k] = getattr(existing, k)
backend\app\db\mysql_generated_daos.py:183: if hasattr(data, api_k) and getattr(data, api_k) is not None:
backend\app\db\mysql_generated_daos.py:185: params[f"s_{api_k}"] = getattr(data, api_k)
backend\scratch\clean_all.py:16: # Pattern: getattr(X, "Y", None) or (X["Y"] ... )
backend\scratch\clean_all.py:22: # Pattern: getattr(X, "Y", getattr(X, "Z", payload.Z))
backend\scratch\clean_all.py:25: # Pattern: getattr(X, "Y", 0.0) -> X.Y
backend\scratch\clean_all.py:28: # Pattern: X["Y"] if isinstance(X, dict) else (getattr(X, "Y", 0)) -> X.Y
backend\scratch\clean_hasattr_final.py:19: content = content.replace('if hasattr(order_data, "couponCode") and order_data.couponCode:', 'if getattr(order_data, "couponCode", None):')
backend\scratch\clean_hasattr_final.py:20: content = content.replace('if hasattr(order_data, "referralCode") and order_data.referralCode:', 'if getattr(order_data, "referralCode", None):')
backend\scratch\clean_hasattr_final.py:21: content = content.replace('elif hasattr(prod, "id"):', 'elif getattr(prod, "id", None):')
backend\scratch\clean_hasattr_final.py:23: content = content.replace('if hasattr(av_id, "id"):', 'if getattr(av_id, "id", None):')
backend\scratch\clean_hasattr_final.py:24: content = content.replace('if hasattr(perms, "serviceableZoneIds"):', 'if getattr(perms, "serviceableZoneIds", None):')
backend\scratch\clean_orders.py:7: # Pattern: X["Y"] if isinstance(X, dict) and "Y" in X else getattr(X, "Y", default)
backend\scratch\clean_orders.py:11: # Pattern: getattr(X, "Y", None) or (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
backend\scratch\clean_orders.py:14: # Pattern: getattr(X, "Y", None) if hasattr(X, "Y") else (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
backend\scratch\code_check.py:8: 'getattr()': [],
backend\scratch\code_check.py:42: if re_getattr.search(line): violations['getattr()'].append(f'{rel}:{i}')
backend\scratch\count_violations.py:8: "getattr()": 0,
backend\scratch\count_violations.py:34: if re_getattr.search(line): counts["getattr()"] += 1
backend\scratch\count_violations2.py:8: "getattr()": [],
backend\scratch\fix_getattr_get.py:11: # Pattern 1: obj.prop if getattr(obj, 'prop', None) is not None else default
backend\scratch\fix_getattr_get.py:12: # E.g. (data.userSegments if getattr(data, 'userSegments', None) is not None else [])
backend\scratch\fix_getattr_get.py:13: # E.g. bool((data.isActive if getattr(data, 'isActive', None) is not None else True))
backend\scratch\fix_getattr_get.py:25: # Pattern 2: getattr(obj, 'prop', default) -> (obj.prop if obj.prop is not None else default)
backend\scratch\fix_getattr_get.py:26: # E.g. getattr(data, 'isActive', True) -> (data.isActive if data.isActive is not None else True)
backend\scratch\fix_getattr_get.py:27: # E.g. getattr(r, 'show_in_mobile_homepage', False) -> (r.show_in_mobile_homepage if r.show_in_mobile_homepage is not None else False)
backend\scratch\fix_getattr_get.py:38: # Pattern 3: getattr(obj, 'prop') -> obj.prop
backend\tests\test_orders_optimization.py:16: if getattr(o, "notes", "") or "".startswith("TEST_ORDER_OPT_") or getattr(o, "notes", "") or "".startswith(
backend\tests\test_orders_optimization.py:19: await order_repository.storage.delete(getattr(o, "id", getattr(o, "_id", None)))
backend\tests\test_orders_optimization.py:24: if getattr(p, "customer_name", getattr(p, "customerName", None)) == "TEST_ORDER_OPT_User":
backend\tests\test_orders_optimization.py:25: await payment_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))
backend\tests\test_orders_optimization.py:30: if getattr(u, "name", None) == "TEST_ORDER_OPT_User" or getattr(u, "email", None) == "opt_user@test.com":
backend\tests\test_orders_optimization.py:31: await user_repository.delete(getattr(u, "id", getattr(u, "_id", None)))
backend\tests\test_orders_optimization.py:36: if getattr(p, "name", None) == "TEST_ORDER_OPT_Product" or getattr(p, "sku", None) == "SKU-OPT-123":
backend\tests\test_orders_optimization.py:37: await product_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))
backend\tests\test_orders_optimization.py:182: ids_p1 = [getattr(o, "id", getattr(o, "_id", None)) for o in p1]
backend\tests\test_orders_optimization.py:183: ids_p2 = [getattr(o, "id", getattr(o, "_id", None)) for o in p2]
backend\tests\test_overall_optimization.py:14: if getattr(u, "name", None) == "TEST_GEN_OPT_User" or getattr(u, "email", None) == "gen_opt_user@test.com":
backend\tests\test_overall_optimization.py:16: await wishlist_repository.storage.deleteMany({"user": getattr(u, "id", getattr(u, "_id", None))})
backend\tests\test_overall_optimization.py:20: await cart_repository.storage.deleteMany({"user": getattr(u, "id", getattr(u, "_id", None))})
backend\tests\test_overall_optimization.py:25: await session_repository.storage.deleteMany({"user": getattr(u, "id", getattr(u, "_id", None))})
backend\tests\test_overall_optimization.py:28: await user_repository.storage.delete(getattr(u, "id", getattr(u, "_id", None)))
backend\tests\test_overall_optimization.py:32: if getattr(p, "name", None) == "TEST_GEN_OPT_Product" or getattr(p, "sku", None) == "SKU-GEN-OPT":
backend\tests\test_overall_optimization.py:33: await product_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))
backend\tests\test_overall_optimization.py:53: if getattr(res, "userId", getattr(res, "user_id", None)) == "TEST_GEN_OPT_USER_ID":
backend\tests\test_overall_optimization.py:54: await store.delete(getattr(res, "id", getattr(res, "_id", None)))
`

## dict_usage (13 hits)
`
fix.py:115: # dict() -> {}
fix.py:118: new_content = new_content.replace('dict()', '{}')
backend\scratch_fix_session.py:7: '''existing_dict = existing.model_dump(exclude_unset=True) if hasattr(existing, 'model_dump') else dict(existing)''',
backend\scratch_fix_session.py:8: '''existing_dict = existing.model_dump(exclude_unset=True, by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)'''
backend\scratch_generate_models.py:46: # Extract keys from the return dict (naively looking for "key":)
backend\scratch_patch_daos.py:11: r'{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else dict(existing)), **\1}',
backend\scratch_patch_slots_dict.py:40: c = c.replace('slot.get("dict")()', 'slot.model_dump() if hasattr(slot, "model_dump") else slot.dict() if hasattr(slot, "dict") else slot')
backend\scratch_patch_update_session.py:10: existing_dict = existing.model_dump(by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)
backend\scratch_patch_users_model_dump.py:5: c = c.replace('user_data.dict(exclude_unset=True)', 'user_data.model_dump(exclude_unset=True, by_alias=True)')
backend\scratch\code_check.py:14: 'dict_cast': [],  # dict(
backend\scratch\count_violations.py:12: "dict() / Dict": 0,
backend\scratch\count_violations.py:38: if re_dict.search(line): counts["dict() / Dict"] += 1
backend\scripts\performance_test.py:51: print(f"  Errors: {dict(error_counts)}")
`

## dot_get (1568 hits)
`
check_history.py:15: for tc in d.get("tool_calls", []):
check_history.py:16: if tc.get("name") in ("replace_file_content", "multi_replace_file_content"):
check_history.py:17: args = tc.get("arguments", {})
check_history.py:18: fpath = args.get("TargetFile", "")
check_targets.py:9: args = call.get('args', {})
check_targets.py:10: tfile = args.get('TargetFile', '')
check_targets.py:12: target = args.get('TargetContent', '')
check_targets2.py:16: args = call.get('args', {})
check_targets2.py:17: tfile = unescape(args.get('TargetFile', ''))
check_targets2.py:19: target = unescape(args.get('TargetContent', ''))
clean_bundle_dicts.py:8: 'bundle_specs = bundle.get("items", []) if isinstance(bundle, dict) else (bundle.items or [])',
clean_bundle_dicts.py:12: 'spec_qty = max(1, (spec.get("quantity", 1) if isinstance(spec, dict) else (spec.quantity if spec.quantity is not None else 1)))',
clean_bundle_dicts.py:16: 'spec_pid = str((spec.get("productId") if isinstance(spec, dict) else spec.productId) or "")',
clean_bundle_dicts.py:20: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))',
clean_orders.py:8: old_users = 'users_map = {str(u.get("id")) if isinstance(u, dict) else str(u.id): u for u in users_list}'
clean_orders.py:13: old_products = 'products_map = {str(p.get("id")) if isinstance(p, dict) else str(p.id): p for p in products_list}'
clean_orders.py:20: oid = str(p.get("orderId", p.get("order_id")))
clean_payment_repo.py:9: # replace (p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None)) with getattr(p, "paymentId", getattr(p, "payment_id", None))
debug_coupons.py:8: print(doc.get("code"), doc.get("method"), doc.get("typeOfDiscount"))
debug_coupons3.py:11: if doc.get("method") == "automatic":
dump_returns.py:11: args = call.get('args', {})
dump_returns.py:12: tfile = args.get('TargetFile', '')
dump_returns.py:14: target = args.get('TargetContent', '')
dump_returns.py:18: rep = args.get('ReplacementContent', '')
extract.py:13: if "CommandLine" in tc.get("args", {}):
extract10.py:17: args = tc.get("args", {})
extract10.py:18: path = args.get("AbsolutePath", "")
extract10.py:24: if next_data.get("type") == "GENERIC" and next_data.get("source") == "MODEL" and "content" in next_data:
extract2.py:21: if "CommandLine" in tc.get("args", {}):
extract3.py:19: args = tc.get("args", {})
extract3.py:21: if tf in args.get("TargetFile", ""):
extract3.py:23: content = args.get("CodeContent", "")
extract4.py:18: if "CommandLine" in tc.get("args", {}):
extract5.py:20: if "output" in data.get("content", "") and ("PERSISTENCE_AUDIT" in data["content"] or "pydantic_scan_report" in data["content"]):
extract6.py:31: cmd = tc.get("args", {}).get("CommandLine", "")
extract8.py:15: args = tc.get("args", {})
extract9.py:14: args = tc.get("args", {})
extract9.py:15: path = args.get("AbsolutePath", "")
extract_edits.py:22: args = call.get('args', {})
extract_edits.py:27: tfile = args.get('TargetFile', '')
extract_edits.py:31: desc = args.get('Description', args.get('Instruction', call['name']))
extract_edits.py:38: chunks = [{'TargetContent': args.get('TargetContent',''), 'ReplacementContent': args.get('ReplacementContent','')}]
extract_edits.py:40: chunks = args.get('ReplacementChunks', [])
extract_edits.py:46: out_f.write(f"--- TARGET ---\n{chunk.get('TargetContent', '')}\n")
extract_edits.py:47: out_f.write(f"--- REPLACEMENT ---\n{chunk.get('ReplacementContent', '')}\n")
find_auth_changes.py:12: for tc in d.get("tool_calls", []):
find_auth_changes.py:13: args = tc.get("arguments", {})
find_auth_changes.py:14: fpath = args.get("TargetFile", "")
find_auth_changes.py:17: print("Tool:", tc.get("name"))
find_auth_changes.py:18: print("StartLine:", args.get("StartLine"))
find_auth_changes.py:19: print("EndLine:", args.get("EndLine"))
find_auth_changes.py:20: print("TargetContent:", repr(args.get("TargetContent", "")))
find_auth_changes.py:21: print("ReplacementContent:", repr(args.get("ReplacementContent", "")))
fix.py:24: idx = text.find('.get(', i)
fix_address.py:9: return f'({var}.get("{attr}") if isinstance({var}, dict) else {var}.{attr})'
fix_all.py:40: create_params_insert = '''                    "assigned_valet": data.get("assignedValet"),
fix_all.py:41: "pending_valet_id": data.get("pendingValetId"),
fix_all.py:42: "valet_assigned_at": _to_ts(data.get("valetAssignedAt")),
fix_all.py:43: "valet_cascade_count": data.get("valetCascadeCount") or 0,
fix_all.py:44: "valet_decline_history": json_dumps(data.get("valetDeclineHistory")) if data.get("valetDeclineHistory") else "[]",'''
fix_all.py:45: content = content.replace('"assigned_valet": data.get("assignedValet"),', create_params_insert, 1)
fix_all.py:48: update_params_insert = '''                    "assigned_valet": merged.get("assignedValet"),
fix_all.py:49: "pending_valet_id": merged.get("pendingValetId"),
fix_all.py:50: "valet_assigned_at": _to_ts(merged.get("valetAssignedAt")),
fix_all.py:51: "valet_cascade_count": merged.get("valetCascadeCount") or 0,
fix_all.py:52: "valet_decline_history": json_dumps(merged.get("valetDeclineHistory")) if merged.get("valetDeclineHistory") else "[]",'''
fix_all.py:57: parts[1] = parts[1].replace('"assigned_valet": merged.get("assignedValet"),', update_params_insert)
fix_all.py:88: old_logic = '''        history = list(ret.get("valetDeclineHistory") or [])
fix_all.py:89: valet_id_str = str(current_user.get("_id"))
fix_all.py:93: new_logic = '''        history = list(ret.get("valetDeclineHistory") or [])
fix_all.py:94: valet_id_str = str(current_user.get("_id"))
fix_all.py:95: if not any(isinstance(d, dict) and d.get("valetId") == valet_id_str for d in history):
fix_all.py:111: history = list(order.get("valetDeclineHistory") or [])
fix_all.py:117: history = list(order.get("valetDeclineHistory") or [])
fix_all.py:118: if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
fix_all.py:124: history = list(ret.get("valetDeclineHistory") or [])
fix_all.py:130: history = list(ret.get("valetDeclineHistory") or [])
fix_all.py:131: if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
fix_bundles_no_get.py:8: content = content.replace('if item.get("product") and item["product"].get("images")', 'if "product" in item and item["product"] and "images" in item["product"] and item["product"]["images"]')
fix_cart_repo.py:6: content = content.replace('cart_dict = {"user": cart_data["user"], "items": cart_data.get("items", [])}\n        cart = CartInternalCreate(**cart_dict)', 'cart = CartInternalCreate(user=cart_data["user"], items=cart_data.get("items", []))')
fix_cod.py:7: content = content.replace('"cod_payment_received": merged.get(\'codPaymentReceived\', merged.get(\'cod_payment_received\')),', '"cod_payment_received": 1 if merged.get(\'codPaymentReceived\', merged.get(\'cod_payment_received\')) else 0,')
fix_cod2.py:7: content = content.replace("1 if merged.get('codPaymentReceived', merged.get('cod_payment_received')) else None", "1 if merged.get('codPaymentReceived', merged.get('cod_payment_received')) else 0")
fix_customer_segment.py:47: if out.get(k) is not None:
fix_customer_segment.py:116: "min_avg_order_value": filters.get("minAverageOrderValue"),
fix_customer_segment.py:117: "max_avg_order_value": filters.get("maxAverageOrderValue"),
fix_customer_segment.py:118: "start_date": filters.get("startDate"),
fix_customer_segment.py:119: "end_date": filters.get("endDate"),
fix_customer_segment.py:120: "min_order_freq": filters.get("minOrderFrequency"),
fix_customer_segment.py:121: "max_order_freq": filters.get("maxOrderFrequency"),
fix_customer_segment.py:122: "state": filters.get("state"),
fix_customer_segment.py:123: "district": filters.get("district"),
fix_customer_segment.py:124: "app_user": filters.get("appUser"),
fix_customer_segment.py:125: "behavior": filters.get("behavior"),
fix_customer_segment.py:126: "role": filters.get("role"),
fix_delivery.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n        for slot in slots:',
fix_delivery_slots_ast.py:9: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])',
fix_delivery_slot_clean.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n    for slot in slots:',
fix_delivery_slot_regex.py:11: r'\1slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n\1for slot in slots:',
fix_display_image.py:19: (item["product"]["images"][0] for item in enriched_items if item.get("product") and item["product"].get("images")),
fix_dues_test5.py:9: content = content.replace('updated_payment.get("paymentEntries", [])', 'updated_payment.payment_entries or []')
fix_generate.py:7: text = text.replace('children_map.get(int(row.id), {})', 'children_map[int(row.id)] if int(row.id) in children_map else {}')
fix_generate.py:8: text = text.replace('children_map.get(int(r.id), {})', 'children_map[int(r.id)] if int(r.id) in children_map else {}')
fix_generate.py:11: text = text.replace('db_col = query_map.get(k, k)', 'db_col = query_map[k] if k in query_map else k')
fix_get.py:9: content = content.replace('item.get("product")', 'item["product"] if "product" in item else None')
fix_get.py:10: content = content.replace('item["product"].get("images")', 'item["product"]["images"] if "images" in item["product"] else None')
fix_get.py:12: # qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)
fix_get.py:13: content = content.replace('item.get("quantity", getattr(item, "quantity", 1))', 'item["quantity"] if "quantity" in item else getattr(item, "quantity", 1)')
fix_get2.py:7: content = content.replace('item.get("productId", item.get("product_id"))', 'item["productId"] if "productId" in item else (item["product_id"] if "product_id" in item else None)')
fix_indent2.py:7: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n        product = await product_repository.findById(p_id)',
fix_indent2.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_indent2.py:11: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)',
fix_indent2.py:12: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_orders_dict.py:18: oid = str(p.get("orderId", p.get("order_id")))
fix_orders_dict.py:32: users_map = {str(u.get("id")) if isinstance(u, dict) else str(u.id): u for u in users_list}
fix_orders_dict.py:41: products_map = {str(p.get("id")) if isinstance(p, dict) else str(p.id): p for p in products_list}
fix_orders_populate.py:38: return obj.get(k, obj.get(k2, default))
fix_order_dao.py:15: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_order_dao_merged.py:17: return f"merged.get('{camel}', merged.get('{snake}'))"
fix_payment_repo2.py:11: entryId=e.get("entryId"),
fix_payment_repo2.py:12: amount=e.get("amount", 0),
fix_payment_repo2.py:13: paymentMethod=e.get("paymentMethod"),
fix_payment_repo2.py:14: paidAt=e.get("paidAt"),
fix_payment_repo2.py:15: image=e.get("image"),
fix_payment_repo2.py:16: notes=e.get("notes"),
fix_payment_repo2.py:17: verified=e.get("verified", False),
fix_payment_repo2.py:18: createdAt=e.get("createdAt")
fix_payment_repo3.py:33: entryId=e.get("entryId"),
fix_payment_repo3.py:34: amount=e.get("amount", 0),
fix_payment_repo3.py:35: paymentMethod=e.get("paymentMethod"),
fix_payment_repo3.py:36: paidAt=e.get("paidAt"),
fix_payment_repo3.py:37: image=e.get("image"),
fix_payment_repo3.py:38: notes=e.get("notes"),
fix_payment_repo3.py:39: verified=e.get("verified", False),
fix_payment_repo3.py:40: createdAt=e.get("createdAt")
fix_printed_bill.py:8: content = content.replace("1 if merged.get('printedBill', merged.get('printed_bill')) else None", "1 if merged.get('printedBill', merged.get('printed_bill')) else 0")
fix_printed_bill.py:9: content = content.replace("1 if merged.get('isUrgentDelivery', merged.get('is_urgent_delivery')) else None", "1 if merged.get('isUrgentDelivery', merged.get('is_urgent_delivery')) else 0")
fix_product_in.py:13: val = query.get("_id", query.get("id"))
fix_product_repo.py:11: "description": data_dict.get("description", ""),
fix_product_repo.py:14: "subCategoryId": data_dict.get("subCategoryId"),
fix_product_repo.py:15: "brandId": data_dict.get("brandId"),
fix_product_repo.py:16: "price": float(data_dict.get("price") if data_dict.get("price") is not None else 0),
fix_product_repo.py:17: "mrp": float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
fix_product_repo.py:18: "stock": int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
fix_product_repo.py:19: "unit": data_dict.get("unit", "pc"),
fix_product_repo.py:20: "isActive": data_dict.get("isActive", True),
fix_product_repo.py:21: "tags": data_dict.get("tags", []),
fix_product_repo.py:22: "images": data_dict.get("images", []),
fix_product_repo.py:23: "thumbnail": data_dict.get("thumbnail"),
fix_product_repo.py:24: "variants": data_dict.get("variantCombinations", []),
fix_product_repo.py:25: "details": data_dict.get("details", {}),
fix_product_repo.py:29: if product.get("variants"):
fix_product_repo.py:34: f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
fix_product_repo.py:47: description=data_dict.get("description", ""),
fix_product_repo.py:50: subCategoryId=data_dict.get("subCategoryId"),
fix_product_repo.py:51: brandId=data_dict.get("brandId"),
fix_product_repo.py:52: price=float(data_dict.get("price") if data_dict.get("price") is not None else 0),
fix_product_repo.py:53: mrp=float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
fix_product_repo.py:54: stock=int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
fix_product_repo.py:55: unit=data_dict.get("unit", "pc"),
fix_product_repo.py:56: isActive=data_dict.get("isActive", True),
fix_product_repo.py:57: tags=data_dict.get("tags", []),
fix_product_repo.py:58: images=data_dict.get("images", []),
fix_product_repo.py:59: thumbnail=data_dict.get("thumbnail"),
fix_product_repo.py:60: variants=data_dict.get("variantCombinations", []),
fix_product_repo.py:61: details=data_dict.get("details", {}),
fix_product_repo.py:69: f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
fix_product_repo2.py:11: "description": data_dict.get("description", ""),
fix_product_repo2.py:14: "subCategoryId": data_dict.get("subCategoryId"),
fix_product_repo2.py:15: "brandId": data_dict.get("brandId"),
fix_product_repo2.py:16: "price": float(data_dict.get("price") if data_dict.get("price") is not None else 0),
fix_product_repo2.py:17: "mrp": float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
fix_product_repo2.py:18: "stock": int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
fix_product_repo2.py:19: "unit": data_dict.get("unit", "pc"),
fix_product_repo2.py:20: "isActive": data_dict.get("isActive", True),
fix_product_repo2.py:21: "tags": data_dict.get("tags", []),
fix_product_repo2.py:22: "images": data_dict.get("images", []),
fix_product_repo2.py:23: "thumbnail": data_dict.get("thumbnail"),
fix_product_repo2.py:24: "variants": data_dict.get("variantCombinations", []),
fix_product_repo2.py:25: "details": data_dict.get("details", {}),
fix_product_repo2.py:29: if product.get("variants"):
fix_product_repo2.py:34: f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
fix_product_repo2.py:47: description=data_dict.get("description", ""),
fix_product_repo2.py:50: subCategoryId=data_dict.get("subCategoryId"),
fix_product_repo2.py:51: brandId=data_dict.get("brandId"),
fix_product_repo2.py:52: price=float(data_dict.get("price") if data_dict.get("price") is not None else 0),
fix_product_repo2.py:53: mrp=float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
fix_product_repo2.py:54: stock=int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
fix_product_repo2.py:55: unit=data_dict.get("unit", "pc"),
fix_product_repo2.py:56: isActive=data_dict.get("isActive", True),
fix_product_repo2.py:57: tags=data_dict.get("tags", []),
fix_product_repo2.py:58: images=data_dict.get("images", []),
fix_product_repo2.py:59: thumbnail=data_dict.get("thumbnail"),
fix_product_repo2.py:60: variants=data_dict.get("variantCombinations", []),
fix_product_repo2.py:61: details=data_dict.get("details", {}),
fix_product_repo2.py:69: f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
fix_segment.py:23: if (isinstance(data, dict) and data.get(k) is not None) or (not isinstance(data, dict) and getattr(data, k, None) is not None):
fix_segment.py:38: if data.get(k) is not None:
fix_sort.py:8: new_code = 'enriched.sort(key=lambda x: (x.get("salesCount", x.get("sales_count")) if x.get("salesCount", x.get("sales_count")) is not None else 0) if isinstance(x, dict) else (x.sales_count if x.sales_count is not None else 0), reverse=True)'
fix_sort2.py:7: old_code = 'enriched.sort(key=lambda x: (x.get("salesCount", x.get("sales_count")) if x.get("salesCount", x.get("sales_count")) is not None else 0) if isinstance(x, dict) else (x.sales_count if x.sales_count is not None else 0), reverse=True)'
fix_sort2.py:8: new_code = 'enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else x.get("sales_count", 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)'
fix_tests_bugs.py:6: c = c.replace('res.get("userId")', 'getattr(res, "userId", getattr(res, "user_id", None))')
fix_user.py:8: content = content.replace('if update_data.email is not None:', 'email_val = update_data.get("email") if isinstance(update_data, dict) else getattr(update_data, "email", None)\n        if email_val is not None:')
fix_user.py:16: content = content.replace('otp_val = payload.otp', 'otp_val = payload.get("otp") if isinstance(payload, dict) else getattr(payload, "otp", None)')
fix_users_ast.py:7: content = content.replace('payload.get("otp")', 'payload["otp"] if "otp" in payload else None')
fix_user_dao2.py:14: # payment_terms = (update_data.get("paymentTerms") if isinstance(update_data, dict) else update_data.payment_terms)
fix_user_dao2.py:20: return obj.get(prop, default)
fix_user_dao3.py:14: content = content.replace("update_data.paymentTerms", "(update_data.get('paymentTerms', update_data.get('payment_terms')) if isinstance(update_data, dict) else getattr(update_data, 'payment_terms', getattr(update_data, 'paymentTerms', None)))")
fix_user_dao3.py:15: content = content.replace("update_data.creditLimit", "(update_data.get('creditLimit', update_data.get('credit_limit')) if isinstance(update_data, dict) else getattr(update_data, 'credit_limit', getattr(update_data, 'creditLimit', None)))")
fix_user_dao3.py:16: content = content.replace("update_data.creditUsed", "(update_data.get('creditUsed', update_data.get('credit_used')) if isinstance(update_data, dict) else getattr(update_data, 'credit_used', getattr(update_data, 'creditUsed', None)))")
fix_user_dao3.py:17: content = content.replace("update_data.approvalStatus", "(update_data.get('approvalStatus', update_data.get('approval_status')) if isinstance(update_data, dict) else getattr(update_data, 'approval_status', getattr(update_data, 'approvalStatus', None)))")
fix_user_dao4.py:8: content = content.replace("update_data.assignedSalesperson", "(update_data.get('assignedSalesperson', update_data.get('assigned_salesperson')) if isinstance(update_data, dict) else getattr(update_data, 'assigned_salesperson', getattr(update_data, 'assignedSalesperson', None)))")
fix_user_dao_final.py:27: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_user_dao_pydantic.py:25: # In update, existing is now UserResponse, so existing.get("name") will crash!
fix_user_dao_pydantic.py:26: # But wait, in fix_user_update.py I used existing.get("name")!
fix_user_in.py:12: val = query.get('_id', query.get('id'))
fix_user_repo.py:9: email_val = update_data.get("email") if isinstance(update_data, dict) else update_data.email
fix_user_repo.py:17: phone_val = update_data.get("phone") if isinstance(update_data, dict) else update_data.phone
fix_user_update.py:17: name = getattr(update_data, "name", existing.get("name"))
fix_user_update.py:18: email = getattr(update_data, "email", existing.get("email"))
fix_user_update.py:19: password_hash = getattr(update_data, "password", existing.get("password_hash"))
fix_user_update.py:20: role = getattr(update_data, "role", existing.get("role"))
fix_user_update.py:21: phone = getattr(update_data, "phone", existing.get("phone"))
fix_user_update.py:22: company_name = getattr(update_data, "companyName", existing.get("companyName"))
fix_user_update.py:23: is_active = getattr(update_data, "isActive", existing.get("isActive"))
fix_user_update.py:24: approval_status = getattr(update_data, "approvalStatus", existing.get("approvalStatus"))
fix_user_update.py:25: is_deactivated = getattr(update_data, "isDeactivated", existing.get("isDeactivated"))
fix_user_update.py:26: credit_limit = getattr(update_data, "creditLimit", existing.get("creditLimit"))
fix_user_update.py:27: credit_used = getattr(update_data, "creditUsed", existing.get("creditUsed"))
fix_user_update.py:28: payment_terms = getattr(update_data, "paymentTerms", existing.get("paymentTerms"))
fix_user_update.py:29: assigned_salesperson = getattr(update_data, "assignedSalesperson", existing.get("assignedSalesperson"))
fix_user_update.py:30: is_email_verified = getattr(update_data, "isEmailVerified", existing.get("isEmailVerified"))
fix_user_update.py:31: referral_code = getattr(update_data, "referralCode", existing.get("referralCode"))
fix_user_update.py:32: is_seller_admin = getattr(update_data, "isSellerAdmin", existing.get("isSellerAdmin"))
fix_user_update.py:33: is_on_duty = getattr(update_data, "isOnDuty", existing.get("isOnDuty"))
fix_user_update.py:34: commission_override_pct = getattr(update_data, "commissionOverridePct", existing.get("commissionOverridePct"))
fix_user_update.py:35: upi_id = getattr(update_data, "upiId", existing.get("upiId"))
fix_user_update.py:36: qr_code_url = getattr(update_data, "qrCodeUrl", existing.get("qrCodeUrl"))
fix_user_update_again.py:8: content = content.replace('existing.get("name")', 'getattr(existing, "name", None)')
fix_user_update_again.py:9: content = content.replace('existing.get("email")', 'getattr(existing, "email", None)')
fix_user_update_again.py:10: content = content.replace('existing.get("password_hash")', 'getattr(existing, "password", None)')
fix_user_update_again.py:11: content = content.replace('existing.get("role")', 'getattr(existing, "role", None)')
fix_user_update_again.py:12: content = content.replace('existing.get("phone")', 'getattr(existing, "phone", None)')
fix_user_update_again.py:13: content = content.replace('existing.get("companyName")', 'getattr(existing, "companyName", None)')
fix_user_update_again.py:14: content = content.replace('existing.get("isActive")', 'getattr(existing, "isActive", None)')
fix_user_update_again.py:15: content = content.replace('existing.get("approvalStatus")', 'getattr(existing, "approvalStatus", None)')
fix_user_update_again.py:16: content = content.replace('existing.get("isDeactivated")', 'getattr(existing, "isDeactivated", None)')
fix_user_update_again.py:17: content = content.replace('existing.get("creditLimit")', 'getattr(existing, "creditLimit", None)')
fix_user_update_again.py:18: content = content.replace('existing.get("creditUsed")', 'getattr(existing, "creditUsed", None)')
fix_user_update_again.py:19: content = content.replace('existing.get("paymentTerms")', 'getattr(existing, "paymentTerms", None)')
fix_user_update_again.py:20: content = content.replace('existing.get("assignedSalesperson")', 'getattr(existing, "assignedSalesperson", None)')
fix_user_update_again.py:21: content = content.replace('existing.get("isEmailVerified")', 'getattr(existing, "isEmailVerified", None)')
fix_user_update_again.py:22: content = content.replace('existing.get("referralCode")', 'getattr(existing, "referralCode", None)')
fix_user_update_again.py:23: content = content.replace('existing.get("isSellerAdmin")', 'getattr(existing, "isSellerAdmin", None)')
fix_user_update_again.py:24: content = content.replace('existing.get("isOnDuty")', 'getattr(existing, "isOnDuty", None)')
fix_user_update_again.py:25: content = content.replace('existing.get("commissionOverridePct")', 'getattr(existing, "commissionOverridePct", None)')
fix_user_update_again.py:26: content = content.replace('existing.get("upiId")', 'getattr(existing, "upiId", None)')
fix_user_update_again.py:27: content = content.replace('existing.get("qrCodeUrl")', 'getattr(existing, "qrCodeUrl", None)')
generate_dao.py:7: flat_config = FLAT_RELATIONAL_DAOS.get(api_name)
generate_dao.py:22: child_tables = conf.get("child_tables", {})
generate_dao.py:72: db_col = query_map.get(k, k)
generate_dao.py:84: return self._map_to_schema(row, children_map.get(int(row.id), {{}}))
generate_dao.py:99: db_col = query_map.get(k, k)
generate_dao.py:114: return [self._map_to_schema(r, children_map.get(int(r.id), {{}})) for r in rows]
patch_bundle_dao_cls.py:12: content = content.replace('(doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id")))', 'doc.external_id if getattr(doc, "external_id", None) is not None else doc.id')
patch_bundle_dao_dict.py:8: '(doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id")))'
patch_bundle_dao_revert.py:7: content = content.replace('doc["items"] = await self._fetch_products((doc["external_id"] if doc["external_id"] is not None else doc["id"]))', 'doc["items"] = await self._fetch_products((doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id"))))')
patch_bundle_repo.py:8: 'if any(getattr(i, "productId", i.get("productId", i.get("product_id")) if isinstance(i, dict) else getattr(i, "product_id", None)) == product_id for i in items):'
patch_bundle_tests2.py:9: content = content.replace('order_response.json().get("_id")', 'order_response.json().get("_id", order_response.json().get("id"))')
patch_dues_test.py:9: content = content.replace('user.get("userId", str(user["_id"]))', 'user.id')
patch_mysql_order_dao_update.py:9: return f'(update_data.get("{attr}") if isinstance(update_data, dict) else update_data.{attr})'
patch_orders4.py:8: 'bundle_specs = bundle.get("items", []) if isinstance(bundle, dict) else (bundle.items or [])'
patch_orders4.py:12: 'spec_qty = max(1, (spec.get("quantity", 1) if isinstance(spec, dict) else (spec.quantity if spec.quantity is not None else 1)))'
patch_orders4.py:16: 'spec_pid = str((spec.get("productId") if isinstance(spec, dict) else spec.productId) or "")'
patch_orders5.py:8: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))\n                    new_sales = (sales_c if sales_c is not None else 0) + copies'
patch_order_clean.py:17: # Replace update_data.<attr> with merged.get('<attr>') in the parameters
patch_order_clean.py:19: return f'merged.get("{match.group(1)}")'
patch_order_repo.py:8: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "out_for_delivery"'
patch_order_repo.py:12: '(update_data.get("shippedAt") if isinstance(update_data, dict) else update_data.shippedAt) is None'
patch_order_repo.py:21: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "delivered"'
patch_order_repo.py:25: '(update_data.get("deliveredAt") if isinstance(update_data, dict) else update_data.deliveredAt) is None'
patch_order_repo.py:33: '(update_data.get("paymentStatus") if isinstance(update_data, dict) else update_data.paymentStatus) is None'
patch_order_repo_fixed.py:9: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_fixed.py:12: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_fixed.py:20: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_fixed.py:29: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_order_repo_replace.py:12: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status)'
patch_order_repo_replace.py:16: '(update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)) is None'
patch_order_repo_replace.py:24: '(update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)) is None'
patch_order_repo_replace.py:32: '(update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)) is None'
patch_order_repo_replace.py:40: '(update_data.get("codPaymentReceived") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceived", None)) is None'
patch_order_repo_replace.py:48: '(update_data.get("codPaymentReceivedAt") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceivedAt", None)) is None'
patch_order_repo_replace.py:60: '(update_data.get("cancelledAt") if isinstance(update_data, dict) else getattr(update_data, "cancelledAt", None)) is None'
patch_order_repo_replace.py:69: 'datetime.fromisoformat((update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt"))'
patch_order_repo_rewrite.py:10: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_rewrite.py:13: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_rewrite.py:21: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_rewrite.py:30: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_payment.py:8: '(p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None))'
patch_routers_bundles.py:9: 'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)'
patch_routers_bundles.py:13: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem('
patch_routers_bundles3.py:8: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)'
patch_routers_bundles_pid.py:7: 'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)',
patch_routers_bundles_pid.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
patch_routers_bundles_pid.py:24: 'available < (item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1))'
patch_routers_bundles_pid.py:28: 'required: {item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)}'
patch_routers_bundles_pid.py:32: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))'
patch_routers_bundles_pid.py:36: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)'
patch_routers_bundles_pid.py:39: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem(',
patch_stock_dao.py:10: res = res.replace('data.productId', 'data.get("productId") if isinstance(data, dict) else getattr(data, "productId", None)')
patch_stock_dao.py:11: res = res.replace('data.userId', 'data.get("userId") if isinstance(data, dict) else getattr(data, "userId", None)')
patch_stock_dao.py:12: res = res.replace('data.quantity', 'data.get("quantity") if isinstance(data, dict) else getattr(data, "quantity", None)')
patch_stock_dao.py:13: res = res.replace('data.status', 'data.get("status") if isinstance(data, dict) else getattr(data, "status", None)')
patch_stock_dao.py:14: res = res.replace('data.expiresAt', 'data.get("expiresAt") if isinstance(data, dict) else getattr(data, "expiresAt", None)')
patch_stock_reservations_dao.py:22: product_id = merged.get("productId") or merged.get("product_id")
patch_stock_reservations_dao.py:27: user_id = merged.get("userId") or merged.get("user_id")
patch_stock_reservations_dao.py:32: quantity = merged.get("quantity")
patch_stock_reservations_dao.py:37: status = merged.get("status")
patch_stock_reservations_dao.py:42: expires_at = merged.get("expiresAt") or merged.get("expires_at")
patch_user_careful.py:23: # Replace merged.something with merged.get("something") in the UPDATE query parameters
patch_user_careful.py:26: line = re.sub(r'merged\.([a-zA-Z0-9_]+)', r'merged.get("\1")', line)
patch_user_careful.py:27: line = line.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_careful.py:28: line = line.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_careful.py:30: '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
patch_user_careful.py:31: '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
patch_user_careful.py:34: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
patch_user_careful.py:35: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
patch_user_careful.py:56: lines[i] = re.sub(r'data\.([a-zA-Z0-9_]+)', r'data_dict.get("\1")', line)
patch_user_children_both.py:14: rep_block = rep_block.replace('data.get(', 'data_dict.get(')
patch_user_clean.py:17: # Replace merged.<attr> with merged.get('<attr>') in the parameters
patch_user_clean.py:19: return f'merged.get("{match.group(1)}")'
patch_user_clean.py:23: content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_clean.py:24: content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_clean.py:28: '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
patch_user_clean.py:29: '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
patch_user_clean.py:32: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
patch_user_clean.py:33: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
patch_user_clean.py:36: # In _replace_children, data is merged, so it is a dict. Replace data.<attr> with data.get("<attr>")
patch_user_clean.py:43: sub_content = sub_content.replace('merged.get("', 'data.get("')
patch_user_dao_bools.py:7: '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
patch_user_dao_bools.py:8: '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
patch_user_dao_bools.py:11: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
patch_user_dao_bools.py:12: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
patch_user_dao_children.py:11: return f'data.get("{attr}")'
patch_user_dao_merged.py:7: # find instances of merged.something and replace with merged.get("something")
patch_user_dao_merged.py:10: return f'merged.get("{attr}")'
patch_user_dao_merged.py:14: content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_dao_merged.py:15: content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_final.py:17: # 2. Patch ONLY the UPDATE sql parameter mapping to use merged.get() instead of merged.<attr>
patch_user_final.py:24: return f'merged.get("{match.group(1)}")'
patch_user_final.py:26: update_block = update_block.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
patch_user_final.py:27: update_block = update_block.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
patch_user_final.py:29: '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
patch_user_final.py:30: '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
patch_user_final.py:33: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
patch_user_final.py:34: '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
patch_user_final.py:38: # 3. Patch _replace_children block to use data.get() instead of data.<attr>
patch_user_final.py:43: return f'data.get("{match.group(1)}")'
patch_zone.py:8: 'if pincode in (zone.get("pincodes", []) if isinstance(zone, dict) else (getattr(zone, "pincodes", []) or [])):'
patch_zone.py:12: '_active_seller_cache[zone.get("id") if isinstance(zone, dict) else zone.id] = list(active)'
recover.py:13: args = call.get('args', {})
recover.py:14: tfile = args.get('TargetFile', '')
recover.py:20: target = args.get('TargetContent', '')
recover.py:24: replacement = args.get('ReplacementContent', '')
recover_crlf.py:18: args = call.get('args', {})
recover_crlf.py:19: tfile = unescape(args.get('TargetFile', ''))
recover_crlf.py:24: target = unescape(args.get('TargetContent', ''))
recover_crlf.py:25: replacement = unescape(args.get('ReplacementContent', ''))
recover_final.py:24: args = call.get('args', {})
recover_final.py:25: tfile = unescape(args.get('TargetFile', ''))
recover_final.py:31: target = unescape(args.get('TargetContent', ''))
recover_final.py:32: replacement = unescape(args.get('ReplacementContent', ''))
recover_fixed.py:19: args = call.get('args', {})
recover_fixed.py:24: tfile = args.get('TargetFile', '')
recover_fixed.py:31: target = args.get('TargetContent', '')
recover_fixed.py:36: replacement = args.get('ReplacementContent', '')
recover_full.py:20: args = call.get('args', {})
recover_full.py:25: tfile = args.get('TargetFile', '')
recover_full.py:32: target = args.get('TargetContent', '')
recover_full.py:37: replacement = args.get('ReplacementContent', '')
recover_full.py:48: chunks = args.get('ReplacementChunks', [])
recover_full.py:59: tc = chunk.get('TargetContent', '')
recover_full.py:60: rc = chunk.get('ReplacementContent', '')
repro_get_bundle.py:17: res = await client.get("/api/bundles/product/1")
rewrite_brand_repo.py:8: name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_brand_repo.py:9: description=getattr(data, 'description', data.get('description') if isinstance(data, dict) else None),
rewrite_brand_repo.py:10: isActive=getattr(data, 'isActive', data.get('isActive') if isinstance(data, dict) else True)
rewrite_repos.py:57: fields = models.get(model_name, [])
rewrite_repos.py:60: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos.py:76: fields = models.get(model_name, [])
rewrite_repos2.py:47: fields = models.get(model_name, [])
rewrite_repos2.py:50: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos2.py:69: fields = models.get(model_name, [])
rewrite_repos3.py:46: fields = models.get(model_name, [])
rewrite_repos3.py:49: mapping.append(f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos3.py:68: fields = models.get(model_name, [])
rewrite_repos4.py:44: #                name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_repos_manual.py:21: fields = models.get(model_name, [])
rewrite_repos_manual.py:32: fields = models.get(model_name, [])
rewrite_repos_manual.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_2.py:21: fields = models.get(model_name, [])
rewrite_repos_manual_2.py:32: fields = models.get(model_name, [])
rewrite_repos_manual_2.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_3.py:21: fields = models.get(model_name, [])
rewrite_repos_manual_3.py:32: fields = models.get(model_name, [])
rewrite_repos_manual_3.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_4.py:21: fields = models.get(model_name, [])
rewrite_repos_manual_5.py:21: fields = models.get(model_name, [])
test_auth_flow.py:19: otp = resp.json().get("otp")
test_auth_flow.py:39: user_data = resp.json().get("user", {})
test_auth_flow.py:40: print("Registered Role:", user_data.get("role"))
test_auth_flow.py:41: print("Registered Company:", user_data.get("companyName"))
test_auth_flow.py:42: print("Registered Approval Status:", user_data.get("approvalStatus"))
test_auth_flow.py:55: token = resp.json().get("token")
test_auth_flow.py:56: resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
test_auth_flow2.py:19: otp = resp.json().get("otp") if resp.status_code == 200 else None
test_auth_flow2.py:39: user_data = resp.json().get("user", {})
test_auth_flow2.py:40: print("Registered Role:", user_data.get("role"))
test_auth_flow2.py:41: print("Effective Role:", user_data.get("effectiveRole"))
test_auth_flow2.py:42: print("Registered Company:", user_data.get("companyName"))
test_auth_flow2.py:43: print("Registered Approval Status:", user_data.get("approvalStatus"))
test_auth_flow2.py:55: token = resp.json().get("token")
test_auth_flow2.py:59: resp = requests.get(f"{BASE_URL}/me", headers={"Authorization": f"Bearer {token}"})
.agents\auditor_m5\audit_get_replacements.py:24: if ".get(" in l:
.agents\auditor_m5\audit_get_replacements.py:33: print(f"Total .get( calls removed across modified routers: {total_get_removed}")
.agents\auditor_m5\deep_attribute_checker.py:76: cls = inline_models.get(ann_str) or SCHEMA_MODELS.get(ann_str) or getattr(mod, ann_str, None)
.agents\auditor_m5\deep_attribute_checker.py:109: # Check .get() calls
.agents\auditor_m5\deep_attribute_checker.py:158: print(f".get() Calls on Payloads: {total_payload_gets}")
.agents\auditor_m5\deep_attribute_checker.py:171: print("\n--- .get() Calls Found on Payloads ---")
.agents\auditor_m5\verify_attributes_and_gets.py:61: print("=== Checking All .get() Calls Across All Routers ===")
.agents\auditor_m5\verify_attributes_and_gets.py:88: print(f"Total .get() calls found across all {len(router_files)} routers: {total_gets}")
.agents\auditor_m5\verify_attributes_and_gets.py:89: print(f"Non-exempt .get() calls found: {len(non_exempt_gets)}")
.agents\explorer_survey_2\generate_report.py:23: f.write("# Router `.get(` Scanner Survey Report\n\n")
.agents\explorer_survey_2\generate_report.py:40: f.write("A complete static and AST analysis was executed across all router files in `backend/app/routers/` to identify, analyze, and categorize every instance of `.get(`.\n\n")
.agents\explorer_survey_2\generate_report.py:44: f.write(f"- **Total `.get(` Instances in Active Routers**: {total_calls}\n")
.agents\explorer_survey_2\generate_report.py:54: f.write("| # | Router File | Cat A (Dict Workarounds) | Cat B (Exempt) | Route Decorators (`@router.get`) | Total `.get(` Calls | Status |\n")
.agents\explorer_survey_2\generate_report.py:59: fcalls = by_file.get(fname, [])
.agents\explorer_survey_2\generate_report.py:80: fcalls = by_file.get(fname, [])
.agents\explorer_survey_2\generate_report.py:133: f.write("Category B encompasses legitimate usages where dictionary `.get()` or method `.get()` is appropriate and exempt from Pydantic model refactoring:\n\n")
.agents\explorer_survey_2\generate_report.py:137: f.write("- **Rationale**: Standard FastAPI route registration decorator (e.g., `@router.get('/summary')`). It is not a dictionary method call.\n\n")
.agents\explorer_survey_2\generate_report.py:141: f.write("  - `activity.py:17`: `request.headers.get('authorization')`\n")
.agents\explorer_survey_2\generate_report.py:142: f.write("  - `activity.py:51`: `request.headers.get('x-session-id')`\n")
.agents\explorer_survey_2\generate_report.py:143: f.write("  - `recommendations.py:334`: `request.headers.get('x-session-id')`\n")
.agents\explorer_survey_2\generate_report.py:148: f.write("  - `content_pages.py:139`: `doc = await about_repository.get()`\n")
.agents\explorer_survey_2\generate_report.py:149: f.write("  - `content_pages.py:145`: `doc = await about_repository.get()`\n")
.agents\explorer_survey_2\generate_report.py:150: f.write("  - `content_pages.py:162`: `doc = await privacy_repository.get()`\n")
.agents\explorer_survey_2\generate_report.py:151: f.write("  - `content_pages.py:168`: `doc = await privacy_repository.get()`\n")
.agents\explorer_survey_2\generate_report.py:152: f.write("  - `content_pages.py:187`: `doc = await privacy_repository.get()`\n")
.agents\explorer_survey_2\generate_report.py:153: f.write("- **Rationale**: Calling the async zero-argument repository method `repo.get()` to fetch the singleton document.\n\n")
.agents\explorer_survey_2\generate_report.py:157: f.write("  - `bundles.py:232`: `product_map.get(str(pid))`\n")
.agents\explorer_survey_2\generate_report.py:158: f.write("  - `cart.py:58`: `products_map.get(str(item.product))`\n")
.agents\explorer_survey_2\generate_report.py:159: f.write("  - `orders.py:224`: `users_map.get(o_user_id)`\n")
.agents\explorer_survey_2\generate_report.py:160: f.write("  - `orders.py:227`: `users_map.get(o_valet_id)`\n")
.agents\explorer_survey_2\generate_report.py:161: f.write("  - `orders.py:230`: `payments_map.get(o_id, [])`\n")
.agents\explorer_survey_2\generate_report.py:162: f.write("  - `orders.py:244`: `products_map.get(prod_id)`\n")
.agents\explorer_survey_2\generate_report.py:163: f.write("  - `orders.py:511`: `_cart_products_map.get(str(item.product or item.product_id))`\n")
.agents\explorer_survey_2\generate_report.py:164: f.write("  - `orders.py:631`: `_cart_products_map.get(str(item.product or item.product_id))`\n")
.agents\explorer_survey_2\generate_report.py:165: f.write("  - `orders.py:1519`: `seller_delivery_map.get(str(seller_id) if seller_id else None)`\n")
.agents\explorer_survey_2\generate_report.py:166: f.write("  - `orders.py:1540`: `seller_docs.get(str(seller_id))`\n")
.agents\explorer_survey_2\generate_report.py:167: f.write("  - `payments.py:217`: `order_map.get(str(payment.order_id))`\n")
.agents\explorer_survey_2\generate_report.py:168: f.write("  - `recommendations.py:91, 97`: `_guest_rec_cache.get(guest_key)`\n")
.agents\explorer_survey_2\generate_report.py:169: f.write("  - `recommendations.py:122`: `cache.get(user_cache_key)`\n")
.agents\explorer_survey_2\generate_report.py:170: f.write("  - `recommendations.py:204, 224`: `product_map.get(pid)`\n")
.agents\explorer_survey_2\generate_report.py:171: f.write("  - `seller_availability.py:141`: `sellers_map.get(sid, {})`\n")
.agents\explorer_survey_2\generate_report.py:172: f.write("  - `users.py:168`: `avail_map.get(vid)`\n")
.agents\explorer_survey_2\generate_report.py:173: f.write("  - `valet_availability.py:208`: `valets_map.get(vid, {})`\n")
.agents\explorer_survey_2\generate_report.py:174: f.write("  - `wishlist.py:64`: `products_map.get(str(item.product))`\n")
.agents\explorer_survey_2\generate_report.py:179: f.write("  - `returns.py:132`: `returned_items_qty[pid] = returned_items_qty.get(pid, 0) + ...`\n")
.agents\explorer_survey_2\generate_report.py:180: f.write("  - `returns.py:148`: `returned_qty = returned_items_qty.get(pid, 0)`\n")
.agents\explorer_survey_2\generate_report.py:185: f.write("  - `version.py:37`: `min_for_platform = min_versions.get(platform_key, config.MIN_APP_VERSION_WEB)`\n")
.agents\explorer_survey_2\generate_report.py:198: f.write("   - `orders.py`: Access `order_data.shippingAddress.state` instead of `order_data.shippingAddress.get('state')`.\n")
.agents\explorer_survey_2\generate_report.py:201: f.write("   - `payments.py`: Replace `entry.get('amount')` with `entry.amount` and `entry.verified`.\n")
.agents\explorer_survey_2\verify_all_classifications.py:10: # 3. repository.get() with 0 arguments (singleton fetch: about_repository, privacy_repository)
.agents\explorer_survey_2\verify_all_classifications.py:35: return "Category B", "Database repository singleton fetch method .get() (Exempt DB query)"
.agents\explorer_survey_2\verify_all_classifications.py:46: return "Category B", f"In-memory dynamic lookup map/cache/tally dictionary: `{caller}.get(...)`"
.agents\explorer_survey_2\verify_all_classifications.py:49: return "Category A", f"Dictionary workaround on payload/model/entity: `{caller}.get({args})`"
.agents\reviewer_m5\list_all_gets.py:59: report_lines.append(f"  [EXEMPT: {exemption_reason}] L{lineno}: {caller}.get({args})")
.agents\reviewer_m5\list_all_gets.py:62: report_lines.append(f"  [VIOLATION] L{lineno}: {caller}.get({args}) | {line}")
.agents\reviewer_m5\verify_routers.py:40: print(f"  AST L{v['line']}: {v['caller']}.get({v['args']})")
.agents\reviewer_m5\verify_routers.py:47: print("\nALL ROUTER FILES HAVE ZERO CATEGORY A .get() VIOLATIONS AND ZERO SIGNATURE VIOLATIONS!")
.agents\worker_m2\dump_violations.py:9: items = data.get(t, [])
.agents\worker_m2\dump_violations.py:16: print(f"  L{lineno}: {caller}.get({args}) -> {line_str}")
backend\check_db_limits.py:10: db_url = os.environ.get("DATABASE_URL")
backend\fix.py:15: 'connect_args["wallet_password"] = os.environ.get("WALLET_PASSWORD", "WalletPassword123#")',
backend\fix.py:16: 'if DATABASE_URL and DATABASE_URL.startswith("oracle"):\n            connect_args["wallet_password"] = os.environ.get("WALLET_PASSWORD", "WalletPassword123#")',
backend\fix_bundles.py:26: r'enriched.sort(key=lambda x: x.get("salesCount", 0), reverse=True)',
backend\fix_db_and_test.py:325: r = await client.get("/users/")
backend\fix_db_and_test.py:335: r = await client.get("/users/", headers={"Authorization": "Bearer invalid.token.here"})
backend\fix_db_and_test.py:345: r = await client.get("/users/", headers={"Authorization": "NotBearer token"})
backend\fix_db_and_test.py:355: r = await client.get("/users/", headers={"Authorization": "Bearer "})
backend\fix_db_and_test.py:433: r = await client.get("/products/public/99999999")
backend\fix_db_and_test.py:443: r = await client.get("/products/public/not-a-valid-id")
backend\fix_db_and_test.py:453: r = await client.get("/products/public?page=-1&limit=10")
backend\fix_db_and_test.py:463: r = await client.get("/products/public?page=1&limit=999999")
backend\fix_db_and_test.py:478: r = await client.get("/users/nonexistent-id")
backend\fix_db_and_test.py:513: r = await client.get("/cart/")
backend\fix_db_and_test.py:548: r = await client.get("/orders/")
backend\fix_db_and_test.py:598: r = await client.get("/products/public?search=<script>alert(1)</script>")
backend\fix_db_and_test.py:652: r = await client.get("/nonexistent-route")
backend\fix_db_and_test.py:708: r = await client.get("/analytics/kpi")
backend\fix_db_and_test.py:718: r = await client.get("/users/pending-approvals")
backend\fix_db_and_test.py:801: r = await client.get("/pincodes/check/000000")
backend\fix_db_and_test.py:816: r = await client.get("/", follow_redirects=True)
backend\fix_db_and_test.py:825: r = await root_client.get(f"http://localhost:{os.getenv('PORT', '8000')}/")
backend\fix_db_and_test.py:854: r = await client.get(f"http://localhost:{os.getenv('PORT', '8000')}/")
backend\fix_mysql_order_dao.py:20: elif 'merged.get(' in line:
backend\fix_mysql_order_dao.py:36: # "ship_name": ((merged.get('shippingAddress', merged.get('shipping_address')) or {})["name"] if "name" in (merged.get('shippingAddress', merged.get('shipping_address')) or {}) else None),
backend\fix_routers.py:25: # The full match is `@router.get("/"...)`
backend\fix_routers.py:28: # The new one we want to prepend is `@router.get(""...)`
backend\fix_routers.py:34: # Match @router.get("/") or @router.get("/", ...)
backend\fix_routers.py:49: # Wait, if we replace, it becomes `@router.get("")\n@router.get("/")`
backend\fix_routers.py:50: # If we run it again, it finds `@router.get("/")` and prepends another `@router.get("")`.
backend\fix_routers.py:51: # Let's clean up any triple or double `@router.get("")`
backend\fix_user_dao_prep.py:16: """"address": children.get("address", {}),
backend\fix_user_dao_prep.py:17: "savedAddresses": children.get("savedAddresses", []),
backend\fix_user_dao_prep.py:24: """"sellerPermissions": children.get("sellerPermissions", {}),
backend\fix_user_dao_prep.py:25: "serviceAreaZones": children.get("serviceAreaZones", []),""",
backend\fix_user_dao_prep.py:61: '"allow_delivery_slots": 1 if data.get("sellerPermissions", {}).get("allowDeliverySlots") else 0, "allow_urgent_delivery": 1 if data.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,',
backend\fix_user_dao_prep.py:67: '"allow_delivery_slots": 1 if merged.get("sellerPermissions", {}).get("allowDeliverySlots") else 0, "allow_urgent_delivery": 1 if merged.get("sellerPermissions", {}).get("allowUrgentDelivery") else 0,',
backend\generate_daos.py:151: code.append("        self.typed_doc_dao = TYPED_DOC_DAOS.get(api_name)")
backend\generate_daos.py:226: code.append("            val = data.get(api_key)")
backend\generate_daos.py:249: code.append('                        params[f"v{i}"] = str(item.get(a_col, ""))')
backend\migrate_events_to_tracking.py:24: existing_keys.add((t.get("type"), t.get("sessionId"), t.get("timestamp")))
backend\migrate_events_to_tracking.py:28: event_type = e.get("type")
backend\migrate_events_to_tracking.py:29: session_id = e.get("sessionId")
backend\migrate_events_to_tracking.py:30: user_id = e.get("userId")
backend\migrate_events_to_tracking.py:31: timestamp = e.get("timestamp")
backend\migrate_events_to_tracking.py:32: payload = e.get("payload") or {}
backend\migrate_events_to_tracking.py:73: doc["isReturning"] = payload.get("returning", False)
backend\migrate_events_to_tracking.py:76: doc["page"] = e.get("page", "/")
backend\migrate_events_to_tracking.py:78: doc["productId"] = payload.get("productId")
backend\migrate_events_to_tracking.py:79: doc["productName"] = payload.get("productName", "Unknown")
backend\migrate_events_to_tracking.py:81: doc["productId"] = payload.get("productId")
backend\migrate_events_to_tracking.py:82: doc["productName"] = payload.get("productName", "Unknown")
backend\migrate_events_to_tracking.py:83: doc["source"] = payload.get("source", "mobile_app")
backend\migrate_events_to_tracking.py:85: doc["productId"] = payload.get("productId")
backend\migrate_events_to_tracking.py:86: doc["quantity"] = payload.get("quantity", 1)
backend\migrate_events_to_tracking.py:88: doc["productId"] = payload.get("productId")
backend\migrate_events_to_tracking.py:89: doc["quantity"] = payload.get("quantity", 1)
backend\migrate_events_to_tracking.py:91: doc["searchTerm"] = payload.get("query", "")
backend\migrate_events_to_tracking.py:92: doc["resultsCount"] = payload.get("resultsCount", 0)
backend\migrate_events_to_tracking.py:95: doc["productId"] = payload.get("productId")
backend\migrate_events_to_tracking.py:101: doc["reason"] = payload.get("reason", "unknown")
backend\refactor.py:28: # We will replace obj.get("key") and obj.get("key", default)
backend\rewrite_orders.py:20: product = await product_repository.findById(item.get("product") or item.get("productId"))
backend\rewrite_orders.py:23: status_code=400, detail=f"Product not found: {item.get('product') or item.get('productId')}"
backend\rewrite_orders.py:25: quantity = item.get("quantity", 0)
backend\rewrite_orders.py:26: sell_as_case = item.get("sellAsCase", False)
backend\rewrite_orders.py:33: product, effective_role, quantity, sell_as_case=sell_as_case, user_id=current_user.get("_id"), ignore_auto_discount=ignore_auto
backend\rewrite_orders.py:82: order_count = await order_repository.countByUser(current_user.get("_id"))
backend\rewrite_orders.py:92: retail_settings = ref_settings.get("retail", {})
backend\rewrite_orders.py:93: if not retail_settings.get("isActive", False) or retail_settings.get("discountValue", 0) <= 0:
backend\rewrite_orders.py:108: if str(referrer.get("_id")) == str(current_user.get("_id")):
backend\rewrite_orders.py:115: discount_type = retail_settings.get("discountType")
backend\rewrite_orders.py:116: discount_value = retail_settings.get("discountValue", 0)
backend\rewrite_orders.py:143: qty_per_case = int(product.get("quantityPerCase") or 1)
backend\rewrite_orders.py:149: gst_percent = product.get("gst", 0) if gst_enabled else 0
backend\rewrite_orders.py:168: "product": product.get("_id"),
backend\rewrite_orders.py:191: prod_res = next((r for r in user_res if r.get("productId") == str(product.get("_id"))), None)
backend\rewrite_orders.py:194: if prod_res and int(prod_res.get("quantity", 0)) >= quantity:
backend\rewrite_orders.py:200: product.get("_id"), exclude_user_id=current_user["_id"]
backend\rewrite_orders.py:206: detail=f"Stock is no longer reserved or available for {product.get('name')}. Please check your cart.",
backend\run_sql.py:10: db_url = os.environ.get("DATABASE_URL")
backend\scratch_add_sellers_dao.py:18: s_id = seller.get("sellerId") if isinstance(seller, dict) else seller.sellerId
backend\scratch_add_sellers_dao.py:19: s_stock = seller.get("stock", 0) if isinstance(seller, dict) else seller.stock
backend\scratch_add_sellers_dao.py:20: s_active = seller.get("isActive", False) if isinstance(seller, dict) else seller.isActive
backend\scratch_add_sellers_dao.py:21: s_status = seller.get("requestStatus", "pending") if isinstance(seller, dict) else seller.requestStatus
backend\scratch_analyze_get.py:15: print("Most common .get() calls (variable, key):")
backend\scratch_analyze_get.py:17: print(f"{var_name}.get('{key}') : {count} times")
backend\scratch_analyze_get2.py:18: print('Most common remaining .get() calls (variable, key):')
backend\scratch_analyze_get2.py:20: print(f'{var_name}.get("{key}") : {count} times')
backend\scratch_append.py:104: new_status = data.get("status", "approved") if data else "approved"
backend\scratch_append.py:132: if data and data.get("notes"):
backend\scratch_append.py:133: target_entry.notes = data.get("notes")
backend\scratch_deep_scan.py:20: print(f"{f}: {m}.get(...)")
backend\scratch_fix_all_gets.py:9: # Replace var.get("key", default)
backend\scratch_fix_all_gets.py:12: # Replace var.get("key")
backend\scratch_fix_all_gets.py:15: # Also wait, some .get() might be chained or inside other expressions.
backend\scratch_fix_all_gets.py:16: # Like item.get(date_field, "") - date_field is a variable!
backend\scratch_fix_all_gets.py:18: # Wait, user said no getattr! I will use \1.__dict__.get(\2, \3)? But it's Pydantic, so \1.model_dump().get(\2, \3)?
backend\scratch_fix_all_gets.py:21: # Let's see if date_field is used. In analytics_repository.py: item.get(date_field, "")
backend\scratch_fix_analytics_repo2.py:7: '''                product = product_map.get(product_id, {})
backend\scratch_fix_analytics_repo2.py:14: '''                product = product_map.get(product_id)
backend\scratch_fix_analytics_repo3.py:11: '''                "name": data.get("name", "Unknown"),
backend\scratch_fix_analytics_repo3.py:12: "productName": data.get("name", "Unknown"),
backend\scratch_fix_analytics_repo3.py:13: "quantity": data.get("quantity", 0),
backend\scratch_fix_analytics_repo3.py:14: "revenue": data.get("revenue", 0),'''
backend\scratch_fix_cohorts.py:7: '''            result.append({"cohort": cohort_month, "months": [cohort_data.get(i, 0) for i in range(max_months + 1)]})''',
backend\scratch_fix_device.py:8: device_type = session_map[session_id].get("deviceType", "unknown").lower()''',
backend\scratch_fix_device.py:11: device_type = s_device.get("type", "unknown").lower()'''
backend\scratch_fix_gets.py:7: 'c_name = child.get("name") if isinstance(child, dict) else child.name',
backend\scratch_fix_gets.py:17: 'ticket.get("user_id") if isinstance(ticket, dict) else getattr(ticket, "user_id", None)',
backend\scratch_fix_gets.py:21: 'ticket.get("userId") if isinstance(ticket, dict) else getattr(ticket, "userId", None)',
backend\scratch_fix_gets.py:25: 'ticket.get("name") if isinstance(ticket, dict) else ticket.name',
backend\scratch_fix_gets.py:29: 'ticket.get("email") if isinstance(ticket, dict) else ticket.email',
backend\scratch_fix_gets.py:33: 'str(ticket.get("id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "id", ""))',
backend\scratch_fix_gets.py:37: 'str(ticket.get("_id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "_id", ""))',
backend\scratch_fix_gets.py:47: 'raw_items = wishlist.get("items", []) if isinstance(wishlist, dict) else (wishlist.items or [])',
backend\scratch_fix_gets.py:51: 'item.get("product") if isinstance(item, dict) else item.product',
backend\scratch_fix_gets.py:55: 'item.get("quantity", 1) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)',
backend\scratch_fix_gets2.py:6: '''cat_dict["gst"] = (cat.gst if hasattr(cat, 'gst') and cat.gst is not None else 0) if not isinstance(cat, dict) else (cat.get("gst", 0))''',
backend\scratch_fix_gets2.py:15: 't_user = ticket.get("user") if isinstance(ticket, dict) else ticket.user',
backend\scratch_fix_gets2.py:19: 't_assigned_to = ticket.get("assignedTo") if isinstance(ticket, dict) else ticket.assignedTo',
backend\scratch_fix_gets2.py:23: 't_responses = ticket.get("responses") if isinstance(ticket, dict) else ticket.responses',
backend\scratch_fix_map_gets.py:6: content = content.replace('product_map.get(product_id, {})', 'product_map.get(product_id)')
backend\scratch_fix_map_gets.py:7: content = content.replace('user_map.get(order.user, {})', 'user_map.get(order.user)')
backend\scratch_fix_map_gets.py:8: content = content.replace('user_map.get(uid, {})', 'user_map.get(uid)')
backend\scratch_fix_map_gets.py:9: content = content.replace('product_map.get(pid, {})', 'product_map.get(pid)')
backend\scratch_fix_map_gets.py:10: content = content.replace('product_map.get(pair[0], {})', 'product_map.get(pair[0])')
backend\scratch_fix_map_gets.py:11: content = content.replace('product_map.get(pair[1], {})', 'product_map.get(pair[1])')
backend\scratch_fix_map_gets.py:12: content = content.replace('order_map.get(ret.orderId, {})', 'order_map.get(ret.orderId)')
backend\scratch_fix_map_gets.py:13: content = content.replace('user_map.get(ret.userId, {})', 'user_map.get(ret.userId)')
backend\scratch_fix_map_gets.py:15: content = content.replace('x.get("createdAt", "")', 'x.get("createdAt") or ""')
backend\scratch_fix_map_gets.py:16: content = content.replace('x.get("createdAt", "") or ""', 'x["createdAt"]') # if it's there
backend\scratch_fix_order_map.py:7: '''            order = order_map.get(ret.orderId, {})
backend\scratch_fix_order_map.py:8: user = user_map.get(ret.userId, {})
backend\scratch_fix_order_map.py:10: refund_value = sum((i.subtotal if i.subtotal is not None else i.get("price", 0)) * (i.quantity if i.quantity is not None else 1) for i in items)
backend\scratch_fix_order_map.py:18: '''            order = order_map.get(ret.orderId)
backend\scratch_fix_order_map.py:19: user = user_map.get(ret.userId)
backend\scratch_fix_product_pair.py:9: product_a = product_map.get(pair[0], {})
backend\scratch_fix_product_pair.py:10: product_b = product_map.get(pair[1], {})
backend\scratch_fix_product_pair.py:19: "productAName": product_a.get("name", "Unknown"),
backend\scratch_fix_product_pair.py:21: "productBName": product_b.get("name", "Unknown"),
backend\scratch_fix_product_pair.py:27: product_a = product_map.get(pair[0])
backend\scratch_fix_product_pair.py:28: product_b = product_map.get(pair[1])
backend\scratch_fix_product_pair_2.py:7: '''                    "productAName": product_a.get("name", "Unknown"),
backend\scratch_fix_product_pair_2.py:8: "productBName": product_b.get("name", "Unknown"),''',
backend\scratch_fix_role_stats.py:10: role = user_role_map.get(uid, "guest" if not uid else "customer")
backend\scratch_fix_role_stats.py:28: role = user_role_map.get(uid, "guest" if not uid else "customer")
backend\scratch_fix_slots_id.py:7: '"slotId": slot.get("id", ""),',
backend\scratch_fix_slots_id.py:8: '"slotId": slot.get("id", f"{slot.get(\'startTime\')}-{slot.get(\'endTime\')}"),'
backend\scratch_fix_slots_id.py:13: 'if slot.get("id") == slot_id:',
backend\scratch_fix_slots_id.py:14: 'if slot.get("id") == slot_id or f"{slot.get(\'startTime\')}-{slot.get(\'endTime\')}" == slot_id:'
backend\scratch_fix_sorted_sessions.py:7: '''            d1 = self._to_naive_utc(self._parse_date(sorted_sessions[i].get("createdAt")))
backend\scratch_fix_sorted_sessions.py:8: d2 = self._to_naive_utc(self._parse_date(sorted_sessions[i + 1].get("createdAt")))''',
backend\scratch_fix_test.py:8: if ev.get("payload", {}) and ev["payload"].get("testRunId") == session_id:
backend\scratch_fix_test.py:11: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test.py:12: if payload and payload.get("testRunId") == session_id:
backend\scratch_fix_test.py:13: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_fix_test2.py:8: if ev.get("payload", {}) and ev["payload"].get("testRunId") == session_id:
backend\scratch_fix_test2.py:11: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test2.py:12: if payload and payload.get("testRunId") == session_id:
backend\scratch_fix_test2.py:13: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_fix_test_again.py:8: payload = ev.payload if hasattr(ev, 'payload') else ev.get("payload", {})
backend\scratch_fix_test_again.py:9: if payload and payload.get("testRunId") == session_id:
backend\scratch_fix_test_again.py:10: ev_id = ev.id if hasattr(ev, 'id') else ev.get("_id")
backend\scratch_fix_user_map.py:7: '''                    "name": user_map[uid].get("name", "Unknown"),
backend\scratch_fix_user_map.py:8: "email": user_map[uid].get("email", "Unknown"),''',
backend\scratch_patch_auth.py:8: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_auth.py:9: c = c.replace('user.get("role")', 'getattr(user, "role", None)')
backend\scratch_patch_auth.py:10: c = c.replace('user.get("isActive")', 'getattr(user, "is_active", True)')
backend\scratch_patch_auth.py:11: c = c.replace('user.get("isEmailVerified")', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_auth_revoked.py:5: c = c.replace('session.get("revokedAt")', 'getattr(session, "revoked_at", None)')
backend\scratch_patch_auth_revoked.py:6: c = c.replace('session.get("revokedReason")', 'getattr(session, "revoked_reason", None)')
backend\scratch_patch_auth_session.py:6: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_available.py:8: replacement = """@router.get("/available", response_model=Any)
backend\scratch_patch_available.py:30: for slot in config.get("slots", []):
backend\scratch_patch_available.py:32: if not (slot.get("isActive") if slot.get("isActive") is not None else True):
backend\scratch_patch_available.py:35: is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not None else False)
backend\scratch_patch_available.py:36: is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None else False)
backend\scratch_patch_available.py:41: slot.get("urgentCutoffHours")
backend\scratch_patch_available.py:42: if slot.get("urgentCutoffHours") is not None
backend\scratch_patch_available.py:43: else slot.get("cutoffHours")
backend\scratch_patch_available.py:46: cutoff_hours = slot.get("cutoffHours")
backend\scratch_patch_available.py:49: anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.get("startTime") or "")
backend\scratch_patch_available.py:60: cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None
backend\scratch_patch_available.py:62: cap = config.get("zoneDefaultCapacity")
backend\scratch_patch_available.py:63: booked = int(slot.get("bookedCount") or 0)
backend\scratch_patch_available.py:68: end_time_str = slot.get("endTime", "")
backend\scratch_patch_available.py:81: "slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),
backend\scratch_patch_available.py:82: "startTime": slot.get("startTime", ""),
backend\scratch_patch_available.py:83: "endTime": slot.get("endTime", ""),
backend\scratch_patch_categories.py:7: # @router.get("/available") returns active_categories
backend\scratch_patch_categories.py:8: c = c.replace('@router.get("/available")', '@router.get("/available", response_model=List[Dict[str, Any]])')
backend\scratch_patch_categories.py:9: c = c.replace('@router.get("/public")', '@router.get("/public", response_model=List[Dict[str, Any]])')
backend\scratch_patch_categories.py:10: c = c.replace('@router.get("/public/tags/{tag_name}/categories")', '@router.get("/public/tags/{tag_name}/categories", response_model=List[Dict[str, Any]])')
backend\scratch_patch_categories.py:11: c = c.replace('@router.get("/public/tags/{tag_name}/brands")', '@router.get("/public/tags/{tag_name}/brands", response_model=List[Dict[str, Any]])')
backend\scratch_patch_categories.py:12: c = re.sub(r'@router\.get\(\"\"\)', r'@router.get("", response_model=List[Dict[str, Any]])', c, count=1)
backend\scratch_patch_categories.py:13: c = re.sub(r'@router\.get\(\"\/\"\)', r'@router.get("/", response_model=List[Dict[str, Any]])', c, count=1)
backend\scratch_patch_categories.py:14: c = c.replace('@router.get("/{category_id}")', '@router.get("/{category_id}", response_model=Dict[str, Any])')
backend\scratch_patch_dao_gets.py:2: c = c.replace('existing.get("stats", {})', '(existing.stats or {})')
backend\scratch_patch_dao_gets.py:6: c = c.replace('existing.get("_db_id")', 'getattr(existing, "_db_id", None)')
backend\scratch_patch_dao_gets.py:10: c = c.replace('doc.get("external_id")', 'getattr(doc, "external_id", getattr(doc, "id", None))')
backend\scratch_patch_dao_returns.py:28: model_name = model_map.get(fp.replace('\\', '/'))
backend\scratch_patch_dao_returns.py:33: model_name = model_map.get(fp.replace('\\', '/'))
backend\scratch_patch_dao_validate.py:24: model_name = model_map.get(fp.replace('\\', '/'))
backend\scratch_patch_dao_zones.py:5: c = c.replace('"serviceAreaZones": children.get("zones", []),', '"serviceAreaZones": children.get("serviceableZoneIds", []),')
backend\scratch_patch_delivery_charge.py:8: 'float(charge_data.get("minCartValue", 0))',
backend\scratch_patch_delivery_charge.py:9: 'float(charge_data.get("minCartValue") or 0)'
backend\scratch_patch_delivery_charge2.py:8: 'float(charge_data.get("charge", 0))',
backend\scratch_patch_delivery_charge2.py:9: 'float(charge_data.get("charge") or 0)'
backend\scratch_patch_delivery_lower.py:8: 'and dc.get("state", "").lower() == state.lower()',
backend\scratch_patch_delivery_lower.py:9: 'and dc.get("state", "").lower() == (state or "").lower()'
backend\scratch_patch_delivery_lower.py:12: 'and dc.get("city", "").lower() == city.lower()',
backend\scratch_patch_delivery_lower.py:13: 'and dc.get("city", "").lower() == (city or "").lower()'
backend\scratch_patch_delivery_lower.py:16: 'and dc.get("district", "").lower() == district.lower()',
backend\scratch_patch_delivery_lower.py:17: 'and dc.get("district", "").lower() == (district or "").lower()'
backend\scratch_patch_dict_access.py:15: # .get() access
backend\scratch_patch_dict_compatible.py:8: return getattr(self, self._get_alias_map().get(key, key), default)
backend\scratch_patch_dict_compatible.py:11: attr_name = self._get_alias_map().get(key, key)
backend\scratch_patch_dict_compatible.py:17: attr_name = self._get_alias_map().get(key, key)
backend\scratch_patch_dict_compatible.py:21: return hasattr(self, self._get_alias_map().get(key, key))
backend\scratch_patch_isActive.py:14: c = c.replace('user.get("isActive", True)', 'getattr(user, "is_active", True)')
backend\scratch_patch_isActive.py:15: c = c.replace('user.get("isEmailVerified", False)', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_isActive.py:20: c = c.replace('user.get("isActive", True)', 'getattr(user, "is_active", True)')
backend\scratch_patch_isActive.py:21: c = c.replace('user.get("isEmailVerified", False)', 'getattr(user, "is_email_verified", False)')
backend\scratch_patch_matched_cap.py:8: '_cap = matched_slot.get("capacity")',
backend\scratch_patch_matched_cap.py:9: '_cap = int(matched_slot.get("capacity")) if matched_slot.get("capacity") not in (None, "") else None'
backend\scratch_patch_matched_cap.py:12: '_cap = matched_config.get("zoneDefaultCapacity")',
backend\scratch_patch_matched_cap.py:13: '_cap = int(matched_config.get("zoneDefaultCapacity")) if matched_config.get("zoneDefaultCapacity") not in (None, "") else None'
backend\scratch_patch_matched_cap.py:16: '_booked = (matched_slot.get("bookedCount") if matched_slot.get("bookedCount") is not None else 0)',
backend\scratch_patch_matched_cap.py:17: '_booked = (int(matched_slot.get("bookedCount")) if matched_slot.get("bookedCount") not in (None, "") else 0)'
backend\scratch_patch_matched_config.py:9: 'str(matched_config.get("_id") or matched_config.get("id") or "")'
backend\scratch_patch_matched_id.py:9: '"slotId": matched_slot.get("id") or f"{matched_slot.get(\'startTime\')}-{matched_slot.get(\'endTime\')}",'
backend\scratch_patch_matched_slot.py:23: camel_prop = camel_map.get(prop, prop)
backend\scratch_patch_matched_slot.py:24: return f'matched_slot.get("{camel_prop}")'
backend\scratch_patch_more.py:5: c = c.replace('user.get("effectiveRole")', 'getattr(user, "effectiveRole", None)')
backend\scratch_patch_orders.py:10: 'seller_ids_in_order = {item.get("sellerId") for item in order_items if isinstance(item, dict) and item.get("sellerId")}'
backend\scratch_patch_orders.py:15: '{item.get("sellerId") for item in order_items if isinstance(item, dict) and item.get("sellerId")}'
backend\scratch_patch_orders2.py:13: if item.get("variantAttributes"):
backend\scratch_patch_orders2.py:14: variant_combos = [{"attributes": item["variantAttributes"], "quantity": item.get("quantity")}]
backend\scratch_patch_orders2.py:18: item.get("quantity"),
backend\scratch_patch_orders2.py:24: new_stock = max(0, ((product.stock if product.stock is not None else 0) or 0) - item.get("quantity"))
backend\scratch_patch_orders3.py:8: # order.id -> order.get("id", order.get("_id"))
backend\scratch_patch_orders3.py:9: c = re.sub(r'order\.id', r'order.get("_id") or order.get("id")', c)
backend\scratch_patch_orders3.py:11: # order.items -> order.get("items")
backend\scratch_patch_orders3.py:12: c = re.sub(r'order\.items', r'order.get("items")', c)
backend\scratch_patch_orders3.py:14: # item.product -> item.get("product")
backend\scratch_patch_orders3.py:15: c = re.sub(r'item\.product', r'item.get("product")', c)
backend\scratch_patch_orders3.py:17: # item.quantity -> item.get("quantity")
backend\scratch_patch_orders3.py:18: c = re.sub(r'item\.quantity', r'item.get("quantity")', c)
backend\scratch_patch_orders4.py:8: # 1. Replace order.id with str(order.get("_id", order.get("id"))) everywhere EXCEPT when it's order_data.id (if any)
backend\scratch_patch_orders4.py:9: c = re.sub(r'\border\.id\b', r'order.get("_id", order.get("id"))', c)
backend\scratch_patch_orders4.py:11: # 2. Replace order.items with order.get("items")
backend\scratch_patch_orders4.py:12: c = re.sub(r'\border\.items\b', r'order.get("items")', c)
backend\scratch_patch_orders4.py:14: # 3. Replace item.product with item.get("product") specifically in the loops over order.get("items")
backend\scratch_patch_orders4.py:16: # `for item in (order.get("items") or []):`
backend\scratch_patch_orders4.py:18: # Since Python dicts support .get(), we'll just fix the lines.
backend\scratch_patch_orders4.py:21: # Find all blocks starting with `for item in (order.get("items") or []):`
backend\scratch_patch_orders4.py:22: # and replace `item.property` with `item.get("property")`
backend\scratch_patch_orders4.py:27: if 'for item in (order.get("items") or []):' in line:
backend\scratch_patch_orders4.py:36: lines[i] = re.sub(r'\bitem\.product\b', r'item.get("product")', lines[i])
backend\scratch_patch_orders4.py:37: lines[i] = re.sub(r'\bitem\.quantity\b', r'item.get("quantity")', lines[i])
backend\scratch_patch_orders4.py:38: lines[i] = re.sub(r'\bitem\.product_id\b', r'item.get("product_id")', lines[i])
backend\scratch_patch_payments.py:7: c = c.replace('@router.get("/dues")', '@router.get("/dues", response_model=DuesResponse)')
backend\scratch_patch_payments.py:8: c = re.sub(r'@router\.get\(\"\"\)', r'@router.get("", response_model=List[Dict[str, Any]])', c, count=1)
backend\scratch_patch_payments.py:9: c = re.sub(r'@router\.get\(\"\/\"\)', r'@router.get("/", response_model=List[Dict[str, Any]])', c, count=1)
backend\scratch_patch_payments.py:10: c = c.replace('@router.get("/{payment_id}")', '@router.get("/{payment_id}", response_model=Dict[str, Any])')
backend\scratch_patch_product_dao.py:10: for tag in data.get("tags") or []:
backend\scratch_patch_product_dao.py:25: {"ext_id": ext_id, "sid": str(s_id), "stock": data.get("stock", 0)}
backend\scratch_patch_product_dao.py:29: s_id = s.get("sellerId")
backend\scratch_patch_product_dao.py:33: {"ext_id": ext_id, "sid": str(s_id), "is_active": 1 if s.get("isActive", True) else 0, "req": s.get("requestStatus", "approved"), "stock": s.get("stock", data.get("stock", 0))}
backend\scratch_patch_product_dao.py:38: for tag in data.get("tags") or []:
backend\scratch_patch_product_repo.py:7: 'cat_gst_map = {cat.get("name"): cat.get("gst", 0) for cat in categories}',
backend\scratch_patch_product_repo.py:8: 'cat_gst_map = {(cat.name if hasattr(cat, "name") else cat.get("name")): (cat.gst if hasattr(cat, "gst") else cat.get("gst", 0)) for cat in categories}'
backend\scratch_patch_prod_bun.py:10: c = c.replace('@router.get("/suggest")', '@router.get("/suggest", response_model=Dict[str, Any])')
backend\scratch_patch_prod_bun.py:15: c = c.replace('@router.get("/{product_id}/search-tags")', '@router.get("/{product_id}/search-tags", response_model=List[Dict[str, Any]])')
backend\scratch_patch_prod_bun.py:25: c = c.replace('@router.get("/search")', '@router.get("/search", response_model=BundlesResponse)')
backend\scratch_patch_prod_bun.py:26: c = re.sub(r'@router\.get\(\"\"\)', r'@router.get("", response_model=BundlesResponse)', c, count=1)
backend\scratch_patch_prod_bun.py:27: c = re.sub(r'@router\.get\(\"\/\"\)', r'@router.get("/", response_model=BundlesResponse)', c, count=1)
backend\scratch_patch_prod_bun.py:28: c = c.replace('@router.get("/product/{product_id}")', '@router.get("/product/{product_id}", response_model=List[Dict[str, Any]])')
backend\scratch_patch_prod_bun.py:29: c = c.replace('@router.get("/admin/all")', '@router.get("/admin/all", response_model=BundlesResponse)')
backend\scratch_patch_prod_bun.py:30: c = c.replace('@router.get("/{bundle_id}")', '@router.get("/{bundle_id}", response_model=Dict[str, Any])')
backend\scratch_patch_repo.py:5: c = c.replace('user.get("password")', 'getattr(user, "password", None)')
backend\scratch_patch_repo.py:6: c = c.replace('user.get("password", "")', 'getattr(user, "password", "")')
backend\scratch_patch_repo.py:7: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_repo.py:9: c = c.replace('user.get("referralCode")', 'getattr(user, "referral_code", None)')
backend\scratch_patch_repo2.py:5: c = c.replace('user.get("savedAddresses", [])', 'getattr(user, "saved_addresses", [])')
backend\scratch_patch_resolve.py:14: zone_id = zone_data.get("_id") or zone_data.get("id") if zone_data else None
backend\scratch_patch_returns_comms.py:6: c = c.replace('@router.get("/order/{order_id}/eligibility")', '@router.get("/order/{order_id}/eligibility", response_model=Dict[str, Any])')
backend\scratch_patch_returns_comms.py:7: c = c.replace('@router.get("/valet/pending")', '@router.get("/valet/pending", response_model=List[Dict[str, Any]])')
backend\scratch_patch_returns_comms.py:13: c = c.replace('@router.get("/tiers")', '@router.get("/tiers", response_model=Dict[str, Any])')
backend\scratch_patch_returns_comms.py:15: c = c.replace('@router.get("/sellers")', '@router.get("/sellers", response_model=Dict[str, Any])')
backend\scratch_patch_returns_comms.py:18: c = c.replace('@router.get("/calculate")', '@router.get("/calculate", response_model=Dict[str, Any])')
backend\scratch_patch_route_order.py:21: # Insert before @router.get("/{user_id}")
backend\scratch_patch_route_order.py:22: insert_idx = c.find('@router.get("/{user_id}"')
backend\scratch_patch_route_order.py:26: print("Could not find @router.get('/{user_id}')")
backend\scratch_patch_route_order_safe.py:18: # Insert before @router.get("/{user_id}")
backend\scratch_patch_route_order_safe.py:19: insert_idx = c.find('@router.get("/{user_id}"')
backend\scratch_patch_route_order_safe.py:23: print("Could not find @router.get('/{user_id}')")
backend\scratch_patch_row_to_dict.py:7: '"variants": children.get("variants", []),',
backend\scratch_patch_row_to_dict.py:8: '"variants": children.get("variants", []),\n            "sellers": children.get("sellers", []),'
backend\scratch_patch_session_dict.py:5: c = c.replace('session.get("lastActiveAt")', 'getattr(session, "last_active_at", None)')
backend\scratch_patch_session_dict.py:7: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_session_dict.py:13: c = c.replace('session.get("status")', 'getattr(session, "status", None)')
backend\scratch_patch_session_dict.py:14: c = c.replace('session.get("_id")', 'getattr(session, "id", None)')
backend\scratch_patch_session_dict.py:15: c = c.replace('user.get("_id")', 'getattr(user, "id", None)')
backend\scratch_patch_session_dict.py:16: c = c.replace('user.get("isDeactivated")', 'getattr(user, "is_deactivated", False)')
backend\scratch_patch_session_dict.py:17: c = c.replace('user.get("role")', 'getattr(user, "role", None)')
backend\scratch_patch_sl.py:23: camel_prop = camel_map.get(prop, prop)
backend\scratch_patch_sl.py:24: return f'sl.get("{camel_prop}")'
backend\scratch_patch_slots_dict.py:20: # We will use `.get()` with camelCase, but since the dot notation used snake_case like `slot.is_active`,
backend\scratch_patch_slots_dict.py:36: camel = mapping.get(prop, prop)
backend\scratch_patch_slots_dict.py:37: return f'slot.get("{camel}")'
backend\scratch_patch_slots_dict.py:40: c = c.replace('slot.get("dict")()', 'slot.model_dump() if hasattr(slot, "model_dump") else slot.dict() if hasattr(slot, "dict") else slot')
backend\scratch_patch_slots_id.py:8: '"slotId": slot.get("id", ""),'
backend\scratch_patch_slots_id.py:12: '"startTime": slot.get("startTime", ""),'
backend\scratch_patch_slots_id.py:16: '"endTime": slot.get("endTime", ""),'
backend\scratch_patch_slots_int.py:7: 'cap = slot.get("capacity")',
backend\scratch_patch_slots_int.py:8: 'cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None'
backend\scratch_patch_slots_int.py:12: 'booked = (slot.get("bookedCount") if slot.get("bookedCount") is not None else 0)',
backend\scratch_patch_slots_int.py:13: 'booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in (None, "") else 0)'
backend\scratch_patch_stragglers.py:4: c = c.replace('@router.get("/valet/pending")', '@router.get("/valet/pending", response_model=List[Dict[str, Any]])')
backend\scratch_patch_stragglers.py:5: c = c.replace('@router.get("/{order_id}/invoice")', '@router.get("/{order_id}/invoice", response_class=FileResponse)')
backend\scratch_patch_stragglers.py:10: c = c.replace('@router.get("/export-csv")', '@router.get("/export-csv", response_class=StreamingResponse)')
backend\scratch_patch_user.py:2: c = c.replace('doc.get("_id")', 'doc.id').replace('doc.get("id")', 'doc.id')
backend\scratch_patch_users.py:10: c = re.sub(r'@router\.get\(\"\"\)', r'@router.get("", response_model=PaginatedUsersResponse)', c, count=1)
backend\scratch_patch_users.py:11: c = re.sub(r'@router\.get\(\"\/\"\)', r'@router.get("/", response_model=PaginatedUsersResponse)', c, count=1)
backend\scratch_patch_users.py:20: c = c.replace('@router.get("/seller-delivery-settings")', '@router.get("/seller-delivery-settings", response_model=Dict[str, Any])')
backend\scratch_patch_users_variables.py:23: 'if existing_with_email and str(existing_with_email.get("_id")) != user_id:',
backend\scratch_patch_zone_id.py:7: 'zone_id = zone_data.get("zoneId") if zone_data else None',
backend\scratch_patch_zone_id.py:8: 'zone_id = zone_data.get("_id") or zone_data.get("id") if zone_data else None'
backend\scratch_product_dao.py:14: sku=v.get("sku"),
backend\scratch_product_dao.py:15: price=v.get("price"),
backend\scratch_product_dao.py:16: pricePerCase=v.get("pricePerCase"),
backend\scratch_product_dao.py:17: stock=v.get("stock", 0),
backend\scratch_product_dao.py:18: attributes=v.get("attributes", {})
backend\scratch_purge_get.py:44: # Pattern: var.get("key", default)
backend\scratch_replace.py:39: content = content.replace(f'.get({old_key})', f'.{new_attr}')
backend\scratch_replace_get.py:6: # Replace simple .get("prop") with .prop
backend\scratch_replace_get.py:10: # Replace .get("prop", default) with (.prop if .prop is not None else default)
backend\scratch_replace_get.py:12: # Because regex for .get("prop", default) is hard to get right if default has parens.
backend\scratch_replace_get.py:16: ('.get("total", 0)', '.total if .total is not None else 0'), # Wait, we need the object! o.get("total", 0) -> o.total if o.total is not None else 0
backend\scratch_scan3.py:20: print(f"{f}: {m[0]}.get(...)")
backend\scratch_sellers_fix.py:37: '"details": children.get("details", {}),',
backend\scratch_sellers_fix.py:38: '"details": children.get("details", {}),\n            "sellers": children.get("sellers", []),',
backend\scratch_strict_ad.py:27: new_type = types_map.get(field_name, 'Optional[str]')
backend\scratch_test_analytics.py:8: 'event_records = [r for r in all_event_records if r.get("payload", {}).get("testRunId") == session_id]',
backend\scratch_test_analytics.py:19: # Are there any other .get() in the test?
backend\scratch_test_analytics.py:21: 'if ev.get("payload", {}).get("testRunId") == session_id:',
backend\scratch_test_analytics.py:22: 'if ev.get("payload", {}) and ev["payload"].get("testRunId") == session_id:'
backend\scratch_test_api.py:11: res = await client.get("/api/delivery-slots/available", params={"pincode": "401847", "segment": "retail", "date": today_str})
backend\scratch_test_db_user.py:13: if u.get("role") == "super_admin" or u.get("email", "").startswith("admin_"):
backend\scratch_test_db_user.py:15: print("Role in Dict:", u.get("role"))
backend\scratch_test_db_user.py:16: user_model = await user_repository.find_by_id(u.get("_id") or str(u.get("id")))
backend\scratch_test_seller_cache.py:12: if not zone or not zone.get('pincodes'):
backend\scratch_test_slots_logic.py:18: for slot in config.get("slots", []):
backend\scratch_test_slots_logic.py:19: if not (slot.get("isActive") if slot.get("isActive") is not None else True):
backend\scratch_test_slots_logic.py:22: is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not None else False)
backend\scratch_test_slots_logic.py:23: is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None else False)
backend\scratch_test_slots_logic.py:29: slot.get("urgentCutoffHours")
backend\scratch_test_slots_logic.py:30: if slot.get("urgentCutoffHours") is not None
backend\scratch_test_slots_logic.py:31: else slot.get("cutoffHours")
backend\scratch_test_slots_logic.py:34: cutoff_hours = slot.get("cutoffHours")
backend\scratch_test_slots_logic.py:37: anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.get("startTime") or "")
backend\scratch_test_slots_logic.py:49: cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None
backend\scratch_test_slots_logic.py:51: cap = config.get("zoneDefaultCapacity")
backend\scratch_test_slots_logic.py:52: booked = int(slot.get("bookedCount") or 0)
backend\scratch_test_slots_logic.py:58: end_time_str = slot.get("endTime", "")
backend\scratch_test_slots_logic.py:71: "slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),
backend\scratch_test_slots_logic.py:72: "startTime": slot.get("startTime", ""),
backend\scratch_test_slots_logic.py:73: "endTime": slot.get("endTime", ""),
backend\scratch_test_zones.py:11: print("Pincodes:", last_zone.get("pincodes"))
backend\scratch_tracking.py:260: product = product_map.get(str(pid))
backend\scratch_tracking.py:348: counts[pid] = counts.get(pid, 0) + 1
backend\scratch_variants.py:24: sku=v.get("sku"),
backend\scratch_variants.py:25: price=v.get("price"),
backend\scratch_variants.py:26: pricePerCase=v.get("pricePerCase"),
backend\scratch_variants.py:27: stock=v.get("stock", 0),
backend\scratch_variants.py:28: attributes=v.get("attributes", {})
backend\seed_20_orders.py:33: customers = [u for u in users if u.get("role") == "customer"]
backend\seed_20_orders.py:34: wholesalers = [u for u in users if u.get("role") == "wholesaler"]
backend\seed_20_orders.py:50: price = product.get("mrp", 10.0)
backend\seed_20_orders.py:85: price = product.get("mrp", 10.0) * 0.8  # Wholesale discount
backend\start_db.py:16: db_url = os.environ.get("DATABASE_URL", "").lower()
backend\start_db.py:21: key_content = os.environ.get("OCI_PRIVATE_KEY", "").replace("\\n", "\n")
backend\start_db.py:26: "user": os.environ.get("OCI_USER_OCID"),
backend\start_db.py:27: "fingerprint": os.environ.get("OCI_FINGERPRINT"),
backend\start_db.py:28: "tenancy": os.environ.get("OCI_TENANCY_OCID"),
backend\start_db.py:29: "region": os.environ.get("OCI_REGION"),
backend\test_auth_http.py:11: otp_val = otp_resp.json().get("otp", "123456")
backend\test_flow2.py:37: tag_id = resp.json().get("_id", "test-tag-id")
backend\test_flow2.py:49: cat_id = resp.json().get("_id", "test-cat-id")
backend\test_flow2.py:61: brand_id = resp.json().get("_id", "test-brand-id")
backend\test_flow2.py:73: col_id = resp.json().get("_id", "test-col-id")
backend\test_flow2.py:95: prod_id = resp.json().get("_id", "test-prod-id")
backend\test_flow2.py:115: bundle_id = resp.json().get("_id", "test-bundle-id")
backend\test_flow3.py:24: otp_val = otp_resp.json().get("otp", "123456")
backend\test_flow3.py:41: admin_token = login_resp.json().get("token")
backend\test_flow3.py:51: promo_id = promo_resp.json().get("_id", promo_resp.json().get("id"))
backend\test_flow3.py:72: banner_id = banner_resp.json().get("_id", banner_resp.json().get("id"))
backend\test_flows_real.py:24: return login_resp.json().get("token")
backend\test_flows_real.py:55: admin_token = login_resp.json().get("token")
backend\test_flow_1.py:20: otp = r.json().get("otp") if r.status_code == 200 else None
backend\whitelist_current_ip.py:32: key_content = os.environ.get("OCI_PRIVATE_KEY", "").replace("\\n", "\n")
backend\whitelist_current_ip.py:37: "user": os.environ.get("OCI_USER_OCID"),
backend\whitelist_current_ip.py:38: "fingerprint": os.environ.get("OCI_FINGERPRINT"),
backend\whitelist_current_ip.py:39: "tenancy": os.environ.get("OCI_TENANCY_OCID"),
backend\whitelist_current_ip.py:40: "region": os.environ.get("OCI_REGION"),
backend\app\main.py:504: @app.get("/")
backend\app\db\mysql_activities_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_activities_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_categoryTags_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_categoryTags_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_coachMarks_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_coachMarks_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_collections_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_collections_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_contacts_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_contacts_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_coupons_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_coupons_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_customer_segment_dao.py:45: if out.get(k) is not None:
backend\app\db\mysql_customer_segment_dao.py:114: "min_avg_order_value": filters.get("minAverageOrderValue"),
backend\app\db\mysql_customer_segment_dao.py:115: "max_avg_order_value": filters.get("maxAverageOrderValue"),
backend\app\db\mysql_customer_segment_dao.py:116: "start_date": filters.get("startDate"),
backend\app\db\mysql_customer_segment_dao.py:117: "end_date": filters.get("endDate"),
backend\app\db\mysql_customer_segment_dao.py:118: "min_order_freq": filters.get("minOrderFrequency"),
backend\app\db\mysql_customer_segment_dao.py:119: "max_order_freq": filters.get("maxOrderFrequency"),
backend\app\db\mysql_customer_segment_dao.py:120: "state": filters.get("state"),
backend\app\db\mysql_customer_segment_dao.py:121: "district": filters.get("district"),
backend\app\db\mysql_customer_segment_dao.py:122: "app_user": filters.get("appUser"),
backend\app\db\mysql_customer_segment_dao.py:123: "behavior": filters.get("behavior"),
backend\app\db\mysql_customer_segment_dao.py:124: "role": filters.get("role"),
backend\app\db\mysql_deliveryChargeDefaults_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_deliveryChargeDefaults_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_deliveryCharges_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_deliveryCharges_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_deliverySlots_dao.py:45: db_col = query_map.get(k, k)
backend\app\db\mysql_deliverySlots_dao.py:57: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_deliverySlots_dao.py:72: db_col = query_map.get(k, k)
backend\app\db\mysql_deliverySlots_dao.py:87: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_deliveryZones_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_deliveryZones_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_deviceSubscriptions_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_deviceSubscriptions_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
backend\app\db\mysql_notifications_dao.py:55: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_notifications_dao.py:85: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_orderFeedback_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_orderFeedback_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_promoStrips_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_promoStrips_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_pushNotifications_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_pushNotifications_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_returnRequests_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_returnRequests_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_returnSettings_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_returnSettings_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_schemes_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_schemes_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_searchTags_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_searchTags_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\db\mysql_supportTickets_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
backend\app\db\mysql_supportTickets_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
backend\app\repositories\collection_repository.py:19: user_role = query.get("userRole", "guest")
backend\app\repositories\collection_repository.py:20: target_page_type = query.get("pageType") or query.get("visiblePage")
backend\app\repositories\collection_repository.py:21: target_page_id = query.get("pageId")
backend\app\repositories\collection_repository.py:51: rule_pg = rule.get("pageType", "")
backend\app\repositories\collection_repository.py:59: page_ids = rule.get("pageIds", [])
backend\app\repositories\content_repository.py:22: existing = await self.get()
backend\app\repositories\content_repository.py:60: existing = await self.get()
backend\app\repositories\google_review_repository.py:42: response = await client.get(url, headers=headers)
backend\app\repositories\google_review_repository.py:45: rating = data.get('rating')
backend\app\repositories\google_review_repository.py:46: count = data.get('userRatingCount')
backend\app\repositories\google_review_repository.py:58: rating_val = res.get("rating", 5.0)
backend\app\repositories\google_review_repository.py:59: count_val = res.get("user_ratings_total", "421")
backend\app\repositories\google_review_repository.py:87: response = await client.get(self.url, headers=headers)
backend\app\repositories\payment_repository.py:179: entryId=e.get("entryId"),
backend\app\repositories\payment_repository.py:180: amount=e.get("amount", 0),
backend\app\repositories\payment_repository.py:181: paymentMethod=e.get("paymentMethod"),
backend\app\repositories\payment_repository.py:182: paidAt=e.get("paidAt"),
backend\app\repositories\payment_repository.py:183: image=e.get("image"),
backend\app\repositories\payment_repository.py:184: notes=e.get("notes"),
backend\app\repositories\payment_repository.py:185: verified=e.get("verified", False),
backend\app\repositories\payment_repository.py:186: createdAt=e.get("createdAt")
backend\app\repositories\payment_repository.py:243: entryId=e.get("entryId"),
backend\app\repositories\payment_repository.py:244: amount=e.get("amount", 0),
backend\app\repositories\payment_repository.py:245: paymentMethod=e.get("paymentMethod"),
backend\app\repositories\payment_repository.py:246: paidAt=e.get("paidAt"),
backend\app\repositories\payment_repository.py:247: image=e.get("image"),
backend\app\repositories\payment_repository.py:248: notes=e.get("notes"),
backend\app\repositories\payment_repository.py:249: verified=e.get("verified", False),
backend\app\repositories\payment_repository.py:250: createdAt=e.get("createdAt")
backend\app\routers\ads.py:23: @router.get("/summary", response_model=AdSummaryResponse)
backend\app\routers\ads.py:44: @router.get("/", response_model=List[Ad])
backend\app\routers\analytics.py:342: @router.get("/kpi", response_model=KPIMetricsResponse)
backend\app\routers\analytics.py:358: @router.get("/dashboard-data", response_model=DashboardDataResponse)
backend\app\routers\analytics.py:373: @router.get("/reports/bundle-performance", response_model=List[UserOrderStatsResponse])
backend\app\routers\analytics.py:385: @router.get("/sales-over-time", response_model=List[SalesOverTimeResponse])
backend\app\routers\analytics.py:403: @router.get("/sales-breakdown", response_model=SalesBreakdownResponse)
backend\app\routers\analytics.py:419: @router.get("/average-order-value", response_model=List[AverageOrderValueResponse])
backend\app\routers\analytics.py:436: @router.get("/sales-by-channel", response_model=List[ItemsByUserTypeResponse])
backend\app\routers\analytics.py:452: @router.get("/sales-by-product", response_model=List[SalesByProductResponse])
backend\app\routers\analytics.py:470: @router.get("/conversion-rate", response_model=ConversionRateResponse)
backend\app\routers\analytics.py:487: @router.get("/conversion-breakdown", response_model=ConversionRateResponse)
backend\app\routers\analytics.py:503: @router.get("/checkout-funnel", response_model=CheckoutFunnelResponse)
backend\app\routers\analytics.py:519: @router.get("/sessions-by-device", response_model=List[SessionsByDeviceResponse])
backend\app\routers\analytics.py:535: @router.get("/sessions-by-location", response_model=List[SessionsByLocationResponse])
backend\app\routers\analytics.py:551: @router.get("/all-user-engagement", response_model=AllUserEngagementResponse)
backend\app\routers\analytics.py:565: @router.get("/products-sell-through", response_model=List[ProductsSellThroughResponse])
backend\app\routers\analytics.py:583: @router.get("/customer-cohort", response_model=List[CustomerCohortResponse])
backend\app\routers\analytics.py:599: @router.get("/sessions-by-landing-page", response_model=List[SessionsByLandingPageResponse])
backend\app\routers\analytics.py:615: @router.get("/user-engagement", response_model=UserEngagementResponse)
backend\app\routers\analytics.py:631: @router.get("/user-engagement/{user_id}", response_model=UserEngagementResponse)
backend\app\routers\analytics.py:651: @router.get("/reports/top-users", response_model=List[TopUsersReportResponse])
backend\app\routers\analytics.py:664: @router.get("/reports/user-order-stats", response_model=List[UserOrderStatsResponse])
backend\app\routers\analytics.py:676: @router.get("/reports/items-by-user-type", response_model=List[ItemsByUserTypeResponse])
backend\app\routers\analytics.py:687: @router.get("/reports/summary", response_model=AllReportsSummaryResponse)
backend\app\routers\analytics.py:698: @router.get("/reports/returns", response_model=List[ReturnsReportResponse])
backend\app\routers\analytics.py:715: @router.get("/reports/payment-methods", response_model=List[PaymentMethodsReportResponse])
backend\app\routers\analytics.py:732: @router.get("/reports/revenue-by-category", response_model=List[PaymentMethodsReportResponse])
backend\app\routers\analytics.py:750: @router.get("/reports/inventory-alerts", response_model=List[RevenueByCategoryResponse])
backend\app\routers\analytics.py:764: @router.get("/reports/fulfillment-time", response_model=List[InventoryAlertResponse])
backend\app\routers\analytics.py:781: @router.get("/reports/coupon-usage", response_model=List[FulfillmentTimeReportResponse])
backend\app\routers\analytics.py:798: @router.get("/reports/sales-by-location", response_model=List[CouponUsageReportResponse])
backend\app\routers\analytics.py:816: @router.get("/reports/new-vs-returning", response_model=List[SalesByLocationReportResponse])
backend\app\routers\analytics.py:832: @router.get("/reports/items-bought-together", response_model=List[NewVsReturningCustomerSalesResponse])
backend\app\routers\analytics.py:849: @router.get("/reports/sales-by-device", response_model=List[ItemsBoughtTogetherResponse])
backend\app\routers\analytics.py:865: @router.get("/reports/top-returned-products", response_model=List[SalesByDeviceReportResponse])
backend\app\routers\analytics.py:883: @router.get("/reports/inventory-value-by-category", response_model=List[TopReturnedProductsResponse])
backend\app\routers\analytics.py:898: @router.get("/reports/sessions-over-time", response_model=List[InventoryValueByCategoryResponse])
backend\app\routers\analytics.py:914: @router.get("/reports/visitors-now", response_model=List[SessionsOverTimeResponse])
backend\app\routers\analytics.py:926: @router.get("/reports/searches-no-clicks", response_model=List[VisitorsNowResponse])
backend\app\routers\analytics.py:942: @router.get("/reports/search-conversion", response_model=List[SearchesNoClicksResponse])
backend\app\routers\analytics.py:958: @router.get("/reports/bounce-rate", response_model=List[SearchConversionResponse])
backend\app\routers\analytics.py:974: @router.get("/reports/rfm-segments", response_model=List[BounceRateResponse])
backend\app\routers\analytics.py:990: @router.get("/reports/customer-frequency", response_model=List[RFMSegmentsResponse])
backend\app\routers\analytics.py:1008: @router.get("/reports/net-sales", response_model=List[CustomerFrequencyResponse])
backend\app\routers\analytics.py:1026: @router.get("/reports/sales-heatmap", response_model=List[NetSalesResponse])
backend\app\routers\analytics.py:1044: @router.get("/reports/inventory-runway", response_model=List[SalesHeatmapResponse])
backend\app\routers\analytics.py:1064: @router.get("/reports/sales-by-channel-detailed", response_model=List[InventoryRunwayResponse])
backend\app\routers\analytics.py:1080: @router.get("/reports/discounts-audit", response_model=List[DiscountsAuditResponse])
backend\app\routers\analytics.py:1098: @router.get("/reports/products-pct-sold", response_model=List[DiscountsAuditResponse])
backend\app\routers\auth.py:577: @router.get("/me", response_model=UserResponse)
backend\app\routers\availability_requests.py:79: @router.get("", response_model=AvailabilityRequestListResponse)
backend\app\routers\availability_requests.py:80: @router.get("/", response_model=AvailabilityRequestListResponse)
backend\app\routers\banners.py:16: @router.get("/public", response_model=List[BannerResponse])
backend\app\routers\banners.py:58: @router.get("", response_model=List[BannerResponse])
backend\app\routers\banners.py:59: @router.get("/", response_model=List[BannerResponse])
backend\app\routers\banners.py:111: @router.get("/{banner_id}", response_model=BannerResponse)
backend\app\routers\brands.py:16: @router.get("/public", response_model=List[BrandResponse])
backend\app\routers\brands.py:36: @router.get("", response_model=List[BrandResponse])
backend\app\routers\brands.py:37: @router.get("/", response_model=List[BrandResponse])
backend\app\routers\bundles.py:175: @router.get("/search", response_model=BundlesListResponse)
backend\app\routers\bundles.py:270: @router.get("", response_model=BundlesListResponse)
backend\app\routers\bundles.py:271: @router.get("/", response_model=BundlesListResponse)
backend\app\routers\bundles.py:289: @router.get("/product/{product_id}", response_model=List[BundleResponse])
backend\app\routers\bundles.py:302: enriched.sort(key=lambda x: x.get("salesCount", 0), reverse=True)
backend\app\routers\bundles.py:309: @router.get("/admin/all", response_model=BundlesListResponse)
backend\app\routers\bundles.py:327: @router.get("/{bundle_id}", response_model=BundleResponse)
backend\app\routers\cart.py:33: @router.get("", response_model=CartResponse)
backend\app\routers\cart.py:34: @router.get("/", response_model=CartResponse)
backend\app\routers\cart.py:369: @router.get("/saved-for-later", response_model=SavedForLaterResponse)
backend\app\routers\categories.py:107: @router.get("/available", response_model=List[Category])
backend\app\routers\categories.py:126: @router.get("/public", response_model=List[Category])
backend\app\routers\categories.py:152: @router.get("/public/tags/{tag_name}/categories", response_model=List[Category])
backend\app\routers\categories.py:179: @router.get("/public/tags/{tag_name}/brands", response_model=List[Any])
backend\app\routers\categories.py:235: @router.get("", response_model=List[Category])
backend\app\routers\categories.py:236: @router.get("/", response_model=List[Category])
backend\app\routers\categories.py:264: @router.get("/{category_id}", response_model=Category)
backend\app\routers\category_tags.py:34: @router.get("", response_model=List[CategoryTagResponse])
backend\app\routers\category_tags.py:35: @router.get("/")
backend\app\routers\category_tags.py:46: @router.get("/active", response_model=List[CategoryTagResponse])
backend\app\routers\coach_marks.py:16: @router.get("", response_model=List[CoachMarkResponse])
backend\app\routers\coach_marks.py:17: @router.get("/", response_model=List[CoachMarkResponse])
backend\app\routers\coach_marks.py:23: @router.get("/{id}", response_model=CoachMarkResponse)
backend\app\routers\collections.py:39: @router.get("/public", response_model=List[CollectionResponse])
backend\app\routers\collections.py:53: @router.get("", response_model=List[CollectionResponse])
backend\app\routers\collections.py:54: @router.get("/", response_model=List[CollectionResponse])
backend\app\routers\collections.py:61: @router.get("/{collection_id}/products", response_model=List[ProductResponse])
backend\app\routers\collections.py:74: @router.get("/{collection_id}", response_model=CollectionResponse)
backend\app\routers\commission.py:232: @router.get("/tiers", response_model=TiersResponse)
backend\app\routers\commission.py:297: @router.get("/sellers", response_model=List[SellerCommissionInfo])
backend\app\routers\commission.py:378: @router.get("/calculate", response_model=CommissionPreviewResponse)
backend\app\routers\contacts.py:16: @router.get("", response_model=List[ContactResponse])
backend\app\routers\contacts.py:17: @router.get("/", response_model=List[ContactResponse])
backend\app\routers\contacts.py:28: @router.get("/public", response_model=List[ContactResponse])
backend\app\routers\contacts.py:36: @router.get("/{contact_id}", response_model=ContactResponse)
backend\app\routers\content_pages.py:100: @router.get("/faq/public", response_model=List[FAQSectionResponse])
backend\app\routers\content_pages.py:106: @router.get("/faq", response_model=List[FAQSectionResponse])
backend\app\routers\content_pages.py:137: @router.get("/about/public", response_model=AboutUsResponse)
backend\app\routers\content_pages.py:140: doc = await about_repository.get()
backend\app\routers\content_pages.py:144: @router.get("/about", response_model=AboutUsResponse)
backend\app\routers\content_pages.py:146: doc = await about_repository.get()
backend\app\routers\content_pages.py:160: @router.get("/privacy/public", response_model=PrivacyPolicyResponse)
backend\app\routers\content_pages.py:163: doc = await privacy_repository.get()
backend\app\routers\content_pages.py:167: @router.get("/privacy", response_model=PrivacyPolicyResponse)
backend\app\routers\content_pages.py:169: doc = await privacy_repository.get()
backend\app\routers\content_pages.py:185: @router.get("/privacy/history", response_model=List[PrivacyPolicyResponse])
backend\app\routers\content_pages.py:188: doc = await privacy_repository.get()
backend\app\routers\coupons.py:16: @router.get("", response_model=List[CouponResponse])
backend\app\routers\coupons.py:17: @router.get("/", response_model=List[CouponResponse])
backend\app\routers\coupons.py:27: @router.get("/validate/{code}", response_model=CouponValidationResponse)
backend\app\routers\coupons.py:88: @router.get("/{coupon_id}", response_model=CouponResponse)
backend\app\routers\customer_segments.py:50: @router.get("", response_model=List[CustomerSegmentResponse])
backend\app\routers\customer_segments.py:51: @router.get("/", response_model=List[CustomerSegmentResponse])
backend\app\routers\customer_segments.py:57: @router.get("/{segment_id}", response_model=CustomerSegmentResponse)
backend\app\routers\delivery_charges.py:75: @router.get("", response_model=List[DeliveryChargeResponse])
backend\app\routers\delivery_charges.py:76: @router.get("/", response_model=List[DeliveryChargeResponse])
backend\app\routers\delivery_charges.py:82: @router.get("/default", response_model=DefaultDeliveryChargeResponse)
backend\app\routers\delivery_charges.py:90: @router.get("/location", response_model=LocationChargeResponse)
backend\app\routers\delivery_charges.py:124: @router.get("/serviceable-pincodes", response_model=List[str])
backend\app\routers\delivery_charges.py:137: @router.get("/check-serviceability", response_model=ServiceabilityResponse)
backend\app\routers\delivery_charges.py:274: @router.get("/{charge_id}", response_model=DeliveryChargeResponse)
backend\app\routers\delivery_slots.py:133: @router.get("", response_model=List[DeliverySlotConfigResponse])
backend\app\routers\delivery_slots.py:134: @router.get("/", response_model=List[DeliverySlotConfigResponse])
backend\app\routers\delivery_slots.py:153: @router.get("/available", response_model=List[AvailableSlotItem])
backend\app\routers\delivery_slots.py:238: @router.get("/dates-with-slots", response_model=DatesWithSlotsResponse)
backend\app\routers\delivery_zones.py:85: @router.get("/for-pincode", response_model=DeliveryZoneResponse)
backend\app\routers\delivery_zones.py:125: @router.get("", response_model=List[DeliveryZoneResponse])
backend\app\routers\delivery_zones.py:126: @router.get("/", response_model=List[DeliveryZoneResponse])
backend\app\routers\delivery_zones.py:156: @router.get("/{zone_id}", response_model=DeliveryZoneResponse)
backend\app\routers\feature_flags.py:43: @router.get("", response_model=List[FeatureFlagItem])
backend\app\routers\feature_flags.py:44: @router.get("/", response_model=List[FeatureFlagItem])
backend\app\routers\feature_flags.py:55: @router.get("/enabled", response_model=List[FeatureFlagItem])
backend\app\routers\feature_flags.py:67: @router.get("/{flag_id}", response_model=FeatureFlagItem)
backend\app\routers\feature_flags.py:82: @router.get("/check/{flag_id}", response_model=FeatureFlagItem)
backend\app\routers\google_reviews.py:22: @router.get("/rating", response_model=GoogleReviewResponse)
backend\app\routers\health.py:38: @router.get("/health/live", response_model=LivenessResponse)
backend\app\routers\health.py:44: @router.get("/health", response_model=HealthResponse)
backend\app\routers\health.py:45: @router.get("/health/ready", response_model=HealthResponse)
backend\app\routers\media.py:39: @router.get("/media", response_class=RedirectResponse)
backend\app\routers\notifications.py:32: @router.get("", response_model=List[NotificationResponse])
backend\app\routers\notifications.py:33: @router.get("/")
backend\app\routers\notifications.py:64: @router.get("/unread-count", response_model=UnreadCountResponse)
backend\app\routers\orders.py:387: @router.get("", response_model=PaginatedOrdersResponse)
backend\app\routers\orders.py:388: @router.get("/", response_model=PaginatedOrdersResponse)
backend\app\routers\orders.py:439: @router.get("/{order_id}", response_model=PopulatedOrderResponse)
backend\app\routers\orders.py:2467: @router.get("/valet/pending", response_model=List[Order])
backend\app\routers\orders.py:3092: @router.get("/{order_id}/invoice", response_class=FileResponse)
backend\app\routers\orders.py:3135: @router.get("/seller-orders", response_model=PaginatedSubOrdersResponse)
backend\app\routers\orders.py:3158: @router.get("/seller-orders/{sub_order_id}", response_model=SubOrder)
backend\app\routers\orders.py:3225: @router.get("/admin/sub-orders", response_model=PaginatedSubOrdersResponse)
backend\app\routers\order_feedback.py:55: @router.get("/eligible", response_model=EligibleFeedbackResponse)
backend\app\routers\order_feedback.py:110: @router.get("/order/{order_id}", response_model=OrderFeedbackResponse)
backend\app\routers\order_feedback.py:127: @router.get("", response_model=List[OrderFeedbackResponse])
backend\app\routers\order_feedback.py:128: @router.get("/", response_model=List[OrderFeedbackResponse])
backend\app\routers\page_info.py:44: @router.get("/{page_id}", response_model=PageInfoResponse)
backend\app\routers\page_info.py:71: @router.get("", response_model=List[PageInfoResponse])
backend\app\routers\page_info.py:72: @router.get("/", response_model=List[PageInfoResponse])
backend\app\routers\payments.py:51: @router.get("/dues", response_model=DuesResponse)
backend\app\routers\payments.py:214: @router.get("", response_model=List[PaymentResponse])
backend\app\routers\payments.py:215: @router.get("/", response_model=List[PaymentResponse])
backend\app\routers\payments.py:254: @router.get("/{payment_id}", response_model=PaymentResponse)
backend\app\routers\pincodes.py:27: @router.get("/states", response_model=List[str])
backend\app\routers\pincodes.py:35: @router.get("/districts", response_model=List[str])
backend\app\routers\pincodes.py:45: @router.get("/pincodes", response_model=List[str])
backend\app\routers\pincodes.py:58: @router.get("/{pincode}", response_model=Dict[str, str])
backend\app\routers\pincode_searches.py:14: @router.get("", response_model=List[PincodeSearchResponse])
backend\app\routers\pincode_searches.py:15: @router.get("/", response_model=List[PincodeSearchResponse])
backend\app\routers\pincode_searches.py:36: @router.get("/stats", response_model=PincodeSearchStatsResponse)
backend\app\routers\products.py:294: @router.get("/export-csv", response_class=StreamingResponse)
backend\app\routers\products.py:413: @router.get("/suggest", response_model=SearchSuggestResponse)
backend\app\routers\products.py:615: @router.get("/public", response_model=PaginatedProductResponse)
backend\app\routers\products.py:732: @router.get("/public/{product_id}", response_model=ProductResponse)
backend\app\routers\products.py:761: @router.get("", response_model=PaginatedProductResponse)
backend\app\routers\products.py:762: @router.get("/", response_model=PaginatedProductResponse)
backend\app\routers\products.py:888: @router.get("/{product_id}", response_model=ProductResponse)
backend\app\routers\products.py:1051: @router.get("/{product_id}/search-tags", response_model=List[str])
backend\app\routers\promo_strips.py:27: @router.get("", response_model=List[PromoStripResponse])
backend\app\routers\promo_strips.py:28: @router.get("/", response_model=List[PromoStripResponse])
backend\app\routers\promo_strips.py:34: @router.get("/active", response_model=List[PromoStripResponse])
backend\app\routers\push_notifications.py:20: @router.get("", response_model=List[PushNotificationResponse])
backend\app\routers\push_notifications.py:21: @router.get("/")
backend\app\routers\push_notifications.py:190: @router.get("/{notification_id}/analytics", response_model=PushAnalyticsResponse)
backend\app\routers\push_notifications.py:212: @router.get("/inbox", response_model=List[PushNotificationResponse])
backend\app\routers\push_notifications.py:268: @router.get("/vapid-public-key", response_model=VapidKeyResponse)
backend\app\routers\push_notifications.py:288: @router.get("/{notification_id}", response_model=PushNotificationResponse)
backend\app\routers\recommendations.py:55: @router.get("", response_model=List[Product])
backend\app\routers\recommendations.py:56: @router.get("/", response_model=List[Product])
backend\app\routers\recommendations.py:138: @router.get("/favourites")
backend\app\routers\recommendations.py:267: @router.get("/metrics")
backend\app\routers\referrals.py:18: @router.get("/settings", response_model=ReferralSettingsResponse)
backend\app\routers\referrals.py:33: @router.get("/check-eligibility", response_model=ReferralEligibilityResponse)
backend\app\routers\referrals.py:105: @router.get("/scheme", response_model=ReferralPublicSchemeResponse)
backend\app\routers\returns.py:71: @router.get("/my-returns", response_model=List[ReturnRequestResponse])
backend\app\routers\returns.py:81: @router.get("/admin/all", response_model=List[ReturnRequestResponse])
backend\app\routers\returns.py:91: @router.get("/valet/assigned", response_model=List[ReturnRequestResponse])
backend\app\routers\returns.py:103: @router.get("/order/{order_id}/eligibility", response_model=ReturnEligibilityResponse)
backend\app\routers\returns.py:432: @router.get("/valet/pending", response_model=List[ReturnRequestResponse])
backend\app\routers\return_settings.py:11: @router.get("", response_model=ReturnSettingsResponse)
backend\app\routers\return_settings.py:12: @router.get("/", response_model=ReturnSettingsResponse)
backend\app\routers\reviews.py:101: @router.get("/product/{product_id}", response_model=List[ProductReviewResponse])
backend\app\routers\reviews.py:112: @router.get("/classifications", response_model=List[ClassificationTagResponse])
backend\app\routers\reviews.py:122: @router.get("/admin/list", response_model=List[ProductReviewResponse])
backend\app\routers\reviews.py:187: @router.get("/admin/classifications", response_model=List[ClassificationTagResponse])
backend\app\routers\schemes.py:19: @router.get("", response_model=List[CouponResponse])
backend\app\routers\schemes.py:20: @router.get("/", response_model=List[CouponResponse])
backend\app\routers\schemes.py:59: @router.get("/applicable/{product_id}", response_model=List[dict])
backend\app\routers\schemes.py:113: @router.get("/applicable/bundle/{bundle_id}", response_model=List[dict])
backend\app\routers\search_tags.py:16: @router.get("", response_model=List[SearchTagResponse])
backend\app\routers\search_tags.py:17: @router.get("/", response_model=List[SearchTagResponse])
backend\app\routers\seller_availability.py:226: @router.get("/my", response_model=List[SellerAvailabilityResponse])
backend\app\routers\seller_availability.py:243: @router.get("", response_model=List[SellerAvailabilityResponse])
backend\app\routers\seller_availability.py:244: @router.get("/", response_model=List[SellerAvailabilityResponse])
backend\app\routers\seller_payouts.py:79: @router.get("", response_model=List[SellerPayoutResponse])
backend\app\routers\seller_payouts.py:80: @router.get("/", response_model=List[SellerPayoutResponse])
backend\app\routers\seller_payouts.py:191: @router.get("/my-summary", response_model=SellerPayoutSummaryResponse)
backend\app\routers\seller_payouts.py:201: @router.get("/summary/{seller_id}", response_model=SellerPayoutSummaryResponse)
backend\app\routers\seller_payouts.py:210: @router.get("/summaries", response_model=List[SellerPayoutSummaryResponse])
backend\app\routers\seller_requests.py:78: @router.get("", response_model=List[SellerRequestResponse])
backend\app\routers\seller_requests.py:79: @router.get("/", response_model=List[SellerRequestResponse])
backend\app\routers\seller_requests.py:99: @router.get("/{request_id}", response_model=SellerRequestResponse)
backend\app\routers\support_tickets.py:108: @router.get("", response_model=List[SupportTicketResponse])
backend\app\routers\support_tickets.py:109: @router.get("/", response_model=List[SupportTicketResponse])
backend\app\routers\support_tickets.py:129: @router.get("/{ticket_id}", response_model=SupportTicketResponse)
backend\app\routers\system_settings.py:33: @router.get("", response_model=SystemSettingsResponse)
backend\app\routers\system_settings.py:34: @router.get("/", response_model=SystemSettingsResponse)
backend\app\routers\tracking.py:323: @router.get("/recent", response_model=List[str])
backend\app\routers\tracking.py:345: @router.get("/suggestions", response_model=SearchSuggestionsResponse)
backend\app\routers\tracking.py:362: @router.get("/most-searched", response_model=List[MostSearchedResponse])
backend\app\routers\tracking.py:375: @router.get("/zero-result-searches", response_model=List[ZeroResultSearchResponse])
backend\app\routers\tracking.py:388: @router.get("/most-viewed", response_model=List[MostViewedResponse])
backend\app\routers\tracking.py:401: @router.get("/returning-users", response_model=List[ReturningUserResponse])
backend\app\routers\tracking.py:413: @router.get("/drop-off-points", response_model=List[DropOffPointResponse])
backend\app\routers\tracking.py:426: @router.get("/cart-abandonments", response_model=List[CartAbandonmentResponse])
backend\app\routers\tracking.py:439: @router.get("/most-abandoned-products", response_model=List[MostAbandonedProductResponse])
backend\app\routers\upi.py:22: @router.get("/details", response_model=UPIDetailsResponse)
backend\app\routers\users.py:17: @router.get("", response_model=PaginatedUsersResponse)
backend\app\routers\users.py:18: @router.get("/", response_model=PaginatedUsersResponse)
backend\app\routers\users.py:63: @router.get("/pending-approvals", response_model=List[UserResponse])
backend\app\routers\users.py:70: @router.get("/me", response_model=UserResponse)
backend\app\routers\users.py:71: @router.get("/profile", response_model=UserResponse)
backend\app\routers\users.py:149: @router.get("/valets/available", response_model=List[UserResponse])
backend\app\routers\users.py:297: @router.get("/seller-delivery-settings", response_model=UserResponse)
backend\app\routers\users.py:352: @router.get("/{user_id}", response_model=UserResponse)
backend\app\routers\valet_availability.py:152: @router.get("/my", response_model=ValetAvailabilityResponse)
backend\app\routers\valet_availability.py:168: @router.get("", response_model=ValetAvailabilityResponse)
backend\app\routers\valet_availability.py:169: @router.get("/", response_model=ValetAvailabilityResponse)
backend\app\routers\valet_payout.py:74: @router.get("/settings", response_model=ValetPayoutSettingsResponse)
backend\app\routers\valet_payout.py:164: @router.get("/earnings/me", response_model=ValetEarningsResponse)
backend\app\routers\valet_payout.py:180: @router.get("/earnings/{valet_id}", response_model=ValetEarningsResponse)
backend\app\routers\version.py:27: @router.get("/version", response_model=VersionResponse)
backend\app\routers\version.py:46: @router.get("/maintenance", response_model=MaintenanceResponse)
backend\app\routers\wishlist.py:37: @router.get("", response_model=List[Product])
backend\app\routers\wishlist.py:38: @router.get("/", response_model=List[Product])
backend\app\services\push_notification_service.py:204: expo_tokens = [d.get("expoToken") for d in targeted_devices if d.get("expoToken")]
backend\app\services\push_notification_service.py:224: web_devices = [d for d in devices if d.get("endpoint") and d.get("keys")]
backend\app\services\push_notification_service.py:237: subscription_info={"endpoint": device.get("endpoint"), "keys": device.get("keys", {})},
backend\app\services\push_notification_service.py:244: logger.error("Failed to send to web device %s: %s", device.get("_id"), str(e))
backend\app\services\push_notification_service.py:246: await push_notification_repository.removeDeviceSubscription(device.get("_id"))
backend\app\services\push_notification_service.py:249: expo_tokens = [d.get("expoToken") for d in devices if d.get("expoToken")]
backend\app\utils\otp.py:87: response = requests.get(url, timeout=10)
backend\load_tests\run_load_tests.py:167: name = row.get("Name", "").strip()
backend\load_tests\run_load_tests.py:180: return float(agg.get(key, default) or default)
backend\load_tests\run_load_tests.py:212: ("P50 response time", stats.get("p50_ms", 9999), SLA["p50_ms"]),
backend\load_tests\run_load_tests.py:213: ("P90 response time", stats.get("p90_ms", 9999), SLA["p90_ms"]),
backend\load_tests\run_load_tests.py:214: ("P99 response time", stats.get("p99_ms", 9999), SLA["p99_ms"]),
backend\load_tests\run_load_tests.py:215: ("Error rate %", stats.get("error_rate_pct", 100), max_err),
backend\load_tests\run_load_tests.py:241: pname = s.get("profile", "?")
backend\load_tests\run_load_tests.py:243: err_msg = s.get("error") or s.get("parse_error", "unknown error")
backend\load_tests\run_load_tests.py:252: s.get("p50_ms", 9999) <= SLA["p50_ms"]
backend\load_tests\run_load_tests.py:253: and s.get("p90_ms", 9999) <= SLA["p90_ms"]
backend\load_tests\run_load_tests.py:254: and s.get("p99_ms", 9999) <= SLA["p99_ms"]
backend\load_tests\run_load_tests.py:255: and s.get("error_rate_pct", 100) <= max_err
backend\load_tests\run_load_tests.py:261: err_pct = s.get("error_rate_pct", 0)
backend\load_tests\run_load_tests.py:264: p50 = s.get("p50_ms", 0)
backend\load_tests\run_load_tests.py:265: p90 = s.get("p90_ms", 0)
backend\load_tests\run_load_tests.py:266: p99 = s.get("p99_ms", 0)
backend\load_tests\run_load_tests.py:274: f"{s.get('total_requests', 0):>10,} "
backend\load_tests\run_load_tests.py:275: f"{s.get('failures', 0):>8,} "
backend\load_tests\run_load_tests.py:277: f"{s.get('rps', 0):>7.1f} "
backend\load_tests\run_load_tests.py:295: pname = s.get("profile", "?")
backend\load_tests\run_load_tests.py:337: resp = httpx.get(f"{BASE_URL}/api/health", timeout=5)
backend\load_tests\run_load_tests.py:348: httpx.get(f"{BASE_URL}{ep}", timeout=10)
backend\load_tests\run_load_tests.py:382: and s.get("p50_ms", 9999) <= SLA["p50_ms"]
backend\load_tests\run_load_tests.py:383: and s.get("p90_ms", 9999) <= SLA["p90_ms"]
backend\load_tests\run_load_tests.py:384: and s.get("p99_ms", 9999) <= SLA["p99_ms"]
backend\load_tests\scenarios\admin_scenario.py:45: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:60: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:82: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:100: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:118: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:135: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:150: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:165: with self.client.get(
backend\load_tests\scenarios\admin_scenario.py:180: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:59: resp = self.client.get(
backend\load_tests\scenarios\customer_scenario.py:66: items = data.get("products", data.get("items", []))
backend\load_tests\scenarios\customer_scenario.py:68: pid = item.get("id") or item.get("productId")
backend\load_tests\scenarios\customer_scenario.py:82: self.client.get(
backend\load_tests\scenarios\customer_scenario.py:90: self.client.get(
backend\load_tests\scenarios\customer_scenario.py:100: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:112: self.client.get("/api/categories/public", name="/api/categories/public")
backend\load_tests\scenarios\customer_scenario.py:120: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:154: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:169: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:184: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:199: with self.client.get(
backend\load_tests\scenarios\customer_scenario.py:216: with self.client.get(
backend\load_tests\scenarios\guest_scenario.py:64: resp = self.client.get(
backend\load_tests\scenarios\guest_scenario.py:71: items = data.get("products", data.get("items", []))
backend\load_tests\scenarios\guest_scenario.py:73: pid = item.get("id") or item.get("productId")
backend\load_tests\scenarios\guest_scenario.py:86: self.client.get("/api/health", name="/api/health")
backend\load_tests\scenarios\guest_scenario.py:91: self.client.get(
backend\load_tests\scenarios\guest_scenario.py:99: self.client.get(
backend\load_tests\scenarios\guest_scenario.py:106: self.client.get("/api/categories/public", name="/api/categories/public")
backend\load_tests\scenarios\guest_scenario.py:110: self.client.get("/api/banners/public", name="/api/banners/public")
backend\load_tests\scenarios\guest_scenario.py:114: self.client.get("/api/brands/public", name="/api/brands/public")
backend\load_tests\scenarios\guest_scenario.py:118: self.client.get("/api/collections/public", name="/api/collections/public")
backend\load_tests\scenarios\guest_scenario.py:122: self.client.get("/api/promo-strips", name="/api/promo-strips")
backend\load_tests\scenarios\guest_scenario.py:126: self.client.get(
backend\load_tests\scenarios\guest_scenario.py:137: with self.client.get(
backend\load_tests\scenarios\guest_scenario.py:150: self.client.get(
backend\load_tests\scenarios\guest_scenario.py:157: self.client.get("/api/search-tags", name="/api/search-tags")
backend\load_tests\scenarios\guest_scenario.py:161: self.client.get("/api/app/version", name="/api/app/version")
backend\scratch\categorize_gets.py:16: # Target of .get(...)
backend\scratch\categorize_gets.py:54: print(f"Total .get() calls found in router function bodies: {len(all_calls)}")
backend\scratch\categorize_gets.py:79: print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")
backend\scratch\categorize_gets.py:81: print(f"\n2. Dict/Map in-memory lookups (e.g. users_map.get(id)): {len(cache_or_map_lookups)}")
backend\scratch\categorize_gets.py:83: print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")
backend\scratch\categorize_gets.py:87: print(f"\n3. Request payload/body .get() calls (DIRECT TARGET FOR R1/R2/R3): {len(payload_or_body_calls)}")
backend\scratch\categorize_gets.py:89: print(f"   {c['file']}:{c['line']} {c['target']}.get({', '.join(c['args'])})")
backend\scratch\categorize_gets.py:91: print(f"\n4. Internal doc/model/record .get() calls: {len(db_doc_or_internal_calls)}")
backend\scratch\categorize_gets.py:98: print(f"      L{c['line']}: {c['target']}.get({', '.join(c['args'])})")
backend\scratch\check_all_gets.py:19: print("\n=== CHECKING ALL .get( IN ROUTERS ===")
backend\scratch\check_all_gets.py:27: if ".get(" in line and not line.strip().startswith("#"):
backend\scratch\check_all_gets.py:29: # filter out @router.get(
backend\scratch\check_all_gets.py:34: print(f"Total non-decorator .get( occurrences: {len(get_usages)}")
backend\scratch\count_violations2.py:31: # .get()
backend\scratch\fix_getattr_get.py:45: # Pattern 5: .get() -> .prop where applicable.
backend\scratch\fix_getattr_get.py:46: # This one is trickier. If it's `payload.get('productId')`, we can change to `payload.productId if payload.productId is not None else None`.
backend\scratch\fix_getattr_get.py:47: # Wait, earlier I proved payload in Pydantic defaults to None or is typed properly. But doing blind `.get()` replacement on ANY dictionary could break things if they are actually python dicts (e.g., query params).
backend\scratch\fix_getattr_get.py:49: # We will skip blind `.get()` replacement to avoid breaking actual dicts, but we will fix `getattr`.
backend\scripts\backfill_product_sellers.py:39: sellers = details.get("sellers", [])
backend\scripts\backfill_product_sellers.py:47: seller_id = str(s.get("sellerId", ""))
backend\scripts\backfill_product_sellers.py:51: is_active_val = s.get("isActive")
backend\scripts\backfill_product_sellers.py:54: req_status = s.get("requestStatus") or "approved"
backend\scripts\backfill_product_sellers.py:56: stock_val = s.get("stock", 0)
backend\scripts\check_super_admin.py:19: print(f"Email: {admin.get('email')}")
backend\scripts\check_super_admin.py:20: print(f"Name: {admin.get('name')}")
backend\scripts\check_super_admin.py:21: print(f"ID: {admin.get('_id')}")
backend\scripts\create_super_admin.py:35: print(f"Email: {existing.get('email')}")
backend\scripts\create_super_admin.py:36: print(f"Name: {existing.get('name')}")
backend\scripts\create_super_admin_direct.py:34: print(f"Email: {existing.get('email')}")
backend\scripts\create_super_admin_direct.py:35: print(f"Name: {existing.get('name')}")
backend\scripts\create_super_admin_direct.py:52: if user.get("userId") and isinstance(user.get("userId"), int):
backend\scripts\create_super_admin_direct.py:53: max_id = max(max_id, user.get("userId", 0))
backend\scripts\fix_super_admin_password.py:39: print(f"Email: {admin.get('email')}")
backend\scripts\fix_super_admin_password.py:42: current_hash = admin.get("password", "")
backend\scripts\fix_super_admin_password.py:51: if admin.get("email") != email.lower():
backend\scripts\load_test.py:14: async with session.get(url, timeout=30) as response:
backend\scripts\load_test.py:58: status_codes[status] = status_codes.get(status, 0) + 1
backend\scripts\load_test.py:61: errors[err] = errors.get(err, 0) + 1
backend\scripts\locustfile.py:9: self.client.get("/api/products/public?limit=20&page=1")
backend\scripts\locustfile.py:13: self.client.get("/api/categories")
backend\scripts\locustfile.py:18: self.client.get(f"/api/products/public?search=pen")
backend\scripts\migrate_option1.py:81: "reason": doc.get("reason"),
backend\scripts\migrate_option1.py:82: "created_by": doc.get("createdBy"),
backend\scripts\migrate_option1.py:83: "cancelled_at": _parse_datetime(doc.get("cancelledAt")),
backend\scripts\migrate_option1.py:153: slot = doc.get("deliverySlot") or {}
backend\scripts\migrate_option1.py:154: c_info = doc.get("couponInfo") or {}
backend\scripts\migrate_option1.py:155: s_addr = doc.get("shippingAddress") or {}
backend\scripts\migrate_option1.py:156: b_addr = doc.get("billingAddress") or {}
backend\scripts\migrate_option1.py:162: "sub_order_number": doc.get("subOrderNumber"),
backend\scripts\migrate_option1.py:163: "parent_order_number": doc.get("parentOrderNumber"),
backend\scripts\migrate_option1.py:164: "seller_name": doc.get("sellerName"),
backend\scripts\migrate_option1.py:165: "subtotal": _safe_float(doc.get("subtotal")),
backend\scripts\migrate_option1.py:166: "tax": _safe_float(doc.get("tax")),
backend\scripts\migrate_option1.py:167: "shipping": _safe_float(doc.get("shipping")),
backend\scripts\migrate_option1.py:168: "delivery_gst": _safe_float(doc.get("deliveryGst")),
backend\scripts\migrate_option1.py:169: "discount": _safe_float(doc.get("discount")),
backend\scripts\migrate_option1.py:170: "order_type": doc.get("orderType"),
backend\scripts\migrate_option1.py:171: "payment_method": doc.get("paymentMethod"),
backend\scripts\migrate_option1.py:172: "is_urgent_delivery": 1 if doc.get("isUrgentDelivery") else 0,
backend\scripts\migrate_option1.py:173: "delivery_slot_config_id": slot.get("configId"),
backend\scripts\migrate_option1.py:174: "delivery_slot_id": slot.get("slotId"),
backend\scripts\migrate_option1.py:175: "delivery_slot_date": slot.get("date"),
backend\scripts\migrate_option1.py:176: "notes": doc.get("notes"),
backend\scripts\migrate_option1.py:177: "coupon_code": doc.get("couponCode"),
backend\scripts\migrate_option1.py:178: "coupon_info_type": c_info.get("discountType"),
backend\scripts\migrate_option1.py:179: "coupon_info_value": _safe_float(c_info.get("discountValue")),
backend\scripts\migrate_option1.py:180: "shipping_name": s_addr.get("name"),
backend\scripts\migrate_option1.py:181: "shipping_phone": s_addr.get("phone"),
backend\scripts\migrate_option1.py:182: "shipping_line1": s_addr.get("line1"),
backend\scripts\migrate_option1.py:183: "shipping_city": s_addr.get("city"),
backend\scripts\migrate_option1.py:184: "shipping_state": s_addr.get("state"),
backend\scripts\migrate_option1.py:185: "shipping_pincode": s_addr.get("pincode"),
backend\scripts\migrate_option1.py:186: "billing_name": b_addr.get("name"),
backend\scripts\migrate_option1.py:187: "billing_phone": b_addr.get("phone"),
backend\scripts\migrate_option1.py:188: "billing_line1": b_addr.get("line1"),
backend\scripts\migrate_option1.py:189: "billing_city": b_addr.get("city"),
backend\scripts\migrate_option1.py:190: "billing_state": b_addr.get("state"),
backend\scripts\migrate_option1.py:191: "billing_pincode": b_addr.get("pincode"),
backend\scripts\migrate_option1.py:192: "delivered_at": _parse_datetime(doc.get("deliveredAt")),
backend\scripts\migrate_option1.py:193: "dispatched_at": _parse_datetime(doc.get("dispatchedAt")),
backend\scripts\migrate_option1.py:194: "cancelled_at": _parse_datetime(doc.get("cancelledAt")),
backend\scripts\migrate_option1.py:200: items = doc.get("items", [])
backend\scripts\migrate_option1.py:206: "product_id": item.get("productId", ""),
backend\scripts\migrate_option1.py:207: "name": item.get("name", ""),
backend\scripts\migrate_option1.py:208: "qty": int(item.get("qty") or 0),
backend\scripts\migrate_option1.py:209: "price": _safe_float(item.get("price")),
backend\scripts\performance_test.py:13: response = await client.get(url, follow_redirects=True)
backend\scripts\performance_test.py:59: await client.get(f"{BASE_URL}/api/health")
backend\scripts\rec_health_test.py:10: response = await client.get(url, follow_redirects=True)
backend\scripts\reset_admin.py:9: print("Found admin:", u.get("email"))
backend\scripts\reset_admin.py:11: await user_repository.update(str(u.get("_id") or u.get("id")), {"password": h})
backend\scripts\reset_super_admin_password.py:40: print(f"Current Email: {admin.get('email')}")
backend\scripts\run_load_test.py:38: "Median (p50)": row.get("Median Response Time", "N/A"),
backend\scripts\run_load_test.py:39: "Average": row.get("Average Response Time", "N/A"),
backend\scripts\run_load_test.py:40: "p90": row.get("90%", "N/A"),
backend\scripts\run_load_test.py:41: "p95": row.get("95%", "N/A"),
backend\scripts\run_load_test.py:42: "p99": row.get("99%", "N/A"),
backend\scripts\run_load_test.py:43: "RPS": row.get("Requests/s", "N/A"),
backend\scripts\run_load_test.py:44: "Failures/s": row.get("Failures/s", "N/A")
backend\scripts\seed_data.py:33: email = existing_admin.get("email", email)
backend\scripts\set_super_admin_email.py:25: print(f"Current Email: {existing.get('email')}")
backend\scripts\set_super_admin_email.py:29: update_data = {"email": email, "name": existing.get("name", "Super Admin")}
backend\scripts\set_super_admin_email.py:36: print(f"Name: {existing.get('name', 'Super Admin')}")
backend\scripts\start_db.py:21: key_content = os.environ.get("OCI_PRIVATE_KEY", "").replace("\\n", "\n")
backend\scripts\start_db.py:26: "user": os.environ.get("OCI_USER_OCID"),
backend\scripts\start_db.py:27: "fingerprint": os.environ.get("OCI_FINGERPRINT"),
backend\scripts\start_db.py:28: "tenancy": os.environ.get("OCI_TENANCY_OCID"),
backend\scripts\start_db.py:29: "region": os.environ.get("OCI_REGION"),
backend\scripts\test_business_flows.py:14: return response.json().get("accessToken")
backend\scripts\test_business_flows.py:22: res = httpx.get(f"{BASE_URL}/health")
backend\scripts\test_e2e_logic.py:15: token = res.json().get("accessToken")
backend\scripts\test_e2e_logic.py:20: res = httpx.get("http://localhost:8000/api/pincodes", headers=headers)
backend\scripts\test_e2e_logic.py:29: res = httpx.get("http://localhost:8000/api/delivery-zones", headers=headers)
backend\scripts\test_e2e_logic.py:38: res = httpx.get("http://localhost:8000/api/delivery-charges", headers=headers)
backend\scripts\test_e2e_logic.py:47: res = httpx.get("http://localhost:8000/api/delivery-charges/check-serviceability?pincode=110001&userRole=retail", headers=headers)
backend\scripts\test_e2e_logic.py:55: res = httpx.get("http://localhost:8000/api/delivery-slots", headers=headers)
backend\scripts\test_password.py:22: hash = admin.get("password", "")
backend\scripts\test_password.py:27: print(f"Email: {admin.get('email')}")
backend\scripts\transfer_categories_brands_tags.py:14: if not os.environ.get("DATABASE_URL"):
backend\scripts\transfer_categories_brands_tags.py:63: eid = doc.get("_id") or doc.get("id")
backend\scripts\transfer_categories_brands_tags.py:66: images = json.dumps(doc.get("images", []), default=str)
backend\scripts\transfer_categories_brands_tags.py:67: sub_categories = json.dumps(doc.get("subCategories", []), default=str)
backend\scripts\transfer_categories_brands_tags.py:68: category_tags = json.dumps(doc.get("categoryTags", []), default=str)
backend\scripts\transfer_categories_brands_tags.py:69: created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
backend\scripts\transfer_categories_brands_tags.py:70: updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
backend\scripts\transfer_categories_brands_tags.py:88: "name": doc.get("name"),
backend\scripts\transfer_categories_brands_tags.py:89: "description": doc.get("description"),
backend\scripts\transfer_categories_brands_tags.py:92: "is_active": 1 if doc.get("isActive", True) else 0,
backend\scripts\transfer_categories_brands_tags.py:93: "category_tag": doc.get("categoryTag"),
backend\scripts\transfer_categories_brands_tags.py:95: "min_qty": doc.get("minimumQuantity", 0),
backend\scripts\transfer_categories_brands_tags.py:96: "show_mobile": 1 if doc.get("showInMobileHomepage", True) else 0,
backend\scripts\transfer_categories_brands_tags.py:97: "gst": float(doc.get("gst", 0.0)),
backend\scripts\transfer_categories_brands_tags.py:98: "is_returnable": 1 if doc.get("isReturnable", False) else 0,
backend\scripts\transfer_categories_brands_tags.py:122: eid = doc.get("_id") or doc.get("id")
backend\scripts\transfer_categories_brands_tags.py:125: created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
backend\scripts\transfer_categories_brands_tags.py:126: updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
backend\scripts\transfer_categories_brands_tags.py:138: "name": doc.get("name"),
backend\scripts\transfer_categories_brands_tags.py:139: "slug": doc.get("slug"),
backend\scripts\transfer_categories_brands_tags.py:140: "image_url": doc.get("imageUrl") or doc.get("image_url"),
backend\scripts\transfer_categories_brands_tags.py:141: "is_active": 1 if doc.get("isActive", True) else 0,
backend\scripts\transfer_categories_brands_tags.py:165: eid = doc.get("_id") or doc.get("id")
backend\scripts\transfer_categories_brands_tags.py:168: created = safe_timestamp(doc.get("createdAt") or doc.get("created_at"))
backend\scripts\transfer_categories_brands_tags.py:169: updated = safe_timestamp(doc.get("updatedAt") or doc.get("updated_at"))
backend\scripts\transfer_categories_brands_tags.py:181: "name": doc.get("name"),
backend\scripts\transfer_categories_brands_tags.py:182: "description": doc.get("description"),
backend\scripts\transfer_categories_brands_tags.py:183: "is_active": 1 if doc.get("isActive", True) else 0,
backend\scripts\update_super_admin.py:35: print(f"Current Email: {existing.get('email')}")
backend\tests\conftest.py:69: token = response.json().get("token", "")
backend\tests\test_analytics_and_tracking.py:23: token = response.json().get("token", "")
backend\tests\test_analytics_and_tracking.py:227: assert res.json().get("status") == "ok"
backend\tests\test_analytics_and_tracking.py:231: event_records = [r for r in all_event_records if r.payload and r.payload.get("testRunId") == session_id]
backend\tests\test_analytics_and_tracking.py:307: res = await client.get("/api/analytics/kpi", headers=admin_auth)
backend\tests\test_analytics_and_tracking.py:313: res = await client.get("/api/analytics/dashboard-data", headers=admin_auth)
backend\tests\test_analytics_and_tracking.py:316: res = await client.get("/api/analytics/conversion-rate", headers=admin_auth)
backend\tests\test_analytics_and_tracking.py:323: res = await client.get("/api/analytics/checkout-funnel", headers=admin_auth)
backend\tests\test_bundle_recommendations.py:44: response = await client.get(f"/api/bundles/product/{pid1}")
backend\tests\test_bundle_recommendations.py:105: order_id = order_response.json().get("_id", order_response.json().get("id"))
backend\tests\test_bxgy_deal_rules.py:66: assert round(validation.get("itemDiscounts", {}).get(0, 0), 2) == 142.86
backend\tests\test_bxgy_deal_rules.py:67: assert round(validation.get("itemDiscounts", {}).get(1, 0), 2) == 57.14
backend\tests\test_cart.py:12: response = await client.get("/api/cart/", headers=user_auth)
backend\tests\test_cart.py:19: response = await client.get("/api/cart/")
backend\tests\test_catalog_routers_pydantic.py:36: paths = schema.get('paths', {})
backend\tests\test_categories.py:41: response = await client.get(f"/api/categories/{category_id}")
backend\tests\test_categories.py:56: response = await client.get("/api/categories/public")
backend\tests\test_categories_optimization.py:11: if cat.get("name", "").startswith("TEST_CAT_OPT_"):
backend\tests\test_core_endpoints.py:24: response = await client.get("/api/users/profile")
backend\tests\test_core_endpoints.py:31: response = await client.get("/api/users/profile", headers=user_auth)
backend\tests\test_core_endpoints.py:40: response = await client.get("/api/orders/", headers=user_auth)
backend\tests\test_core_endpoints.py:47: response = await client.get("/api/wishlist/", headers=user_auth)
backend\tests\test_core_endpoints.py:54: response = await client.get("/api/categories/public")
backend\tests\test_core_endpoints.py:63: response = await client.get("/api/brands/public")
backend\tests\test_core_endpoints.py:71: response = await client.get("/api/payments/status/nonexistent-order-id", headers=user_auth)
backend\tests\test_core_endpoints.py:78: response = await client.get("/api/returns/my-returns", headers=user_auth)
backend\tests\test_core_endpoints.py:85: response = await client.get("/api/analytics/kpi", headers=user_auth)
backend\tests\test_core_endpoints.py:92: response = await client.get("/api/support-tickets/")
backend\tests\test_core_endpoints.py:117: response = await client.get("/api/support-tickets/", headers=user_auth)
backend\tests\test_core_endpoints.py:122: response = await client.get(f"/api/support-tickets/{ticket_id}", headers=user_auth)
backend\tests\test_coupon_mode.py:101: print("Discount:", c.get("method"), c.get("isActive"), c.get("typeOfDiscount"), c.get("appliesToValueIds"))
backend\tests\test_delivery_zones_and_checkout.py:256: resp = await client.get("/api/delivery-zones/for-pincode?pincode=000000")
backend\tests\test_delivery_zones_and_checkout.py:277: resp = await client.get("/api/delivery-charges")
backend\tests\test_delivery_zones_and_checkout.py:285: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:309: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:377: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:416: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:457: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:497: resp = await client.get(
backend\tests\test_delivery_zones_and_checkout.py:729: resp = await client.get("/api/delivery-zones")
backend\tests\test_delivery_zones_and_checkout.py:772: resp = await client.get("/api/delivery-slots")
backend\tests\test_discount_overlap.py:16: response = await client.get("/api/coupons/")
backend\tests\test_e2e.py:82: valet_res = await client.get("/api/auth/me", headers=valet_auth)
backend\tests\test_e2e.py:84: valet2_res = await client.get("/api/auth/me", headers=valet2_auth)
backend\tests\test_e2e.py:124: seller_user_res = await client.get("/api/auth/me", headers=seller_auth)
backend\tests\test_e2e.py:152: res = await client.get("/api/delivery-slots/available", params={"pincode": test_pincode, "segment": "retail", "date": today_str})
backend\tests\test_e2e.py:181: res = await client.get(f"/api/orders/{order_id}", headers=admin_auth)
backend\tests\test_email_verification.py:15: res = await client.get("/api/users/profile", headers=user_auth)
backend\tests\test_email_verification.py:18: assert profile.get("isEmailVerified") is False
backend\tests\test_email_verification.py:38: res = await client.get("/api/users/profile", headers=user_auth)
backend\tests\test_email_verification.py:41: assert profile.get("isEmailVerified") is True
backend\tests\test_email_verification.py:47: res = await client.get("/api/users/profile", headers=user_auth)
backend\tests\test_email_verification.py:52: res = await client.get("/api/users/profile", headers=user_auth)
backend\tests\test_email_verification.py:53: assert res.json().get("isEmailVerified") is True
backend\tests\test_email_verification.py:59: assert res.json().get("isEmailVerified") is True
backend\tests\test_email_verification.py:67: assert res.json().get("isEmailVerified") is False
backend\tests\test_flow3.py:28: banner_id = created.get("_id")
backend\tests\test_flow3.py:32: response = await client.get("/api/banners/")
backend\tests\test_flow3.py:36: response = await client.get("/api/banners/public?position=homepage_web&userRole=customer")
backend\tests\test_flow3.py:56: promo_id = created.get("_id")
backend\tests\test_flow3.py:60: response = await client.get("/api/promo-strips/")
backend\tests\test_flow3.py:64: response = await client.get("/api/promo-strips/active")
backend\tests\test_health.py:13: response = await client.get("/api/health")
backend\tests\test_health.py:24: response = await client.get("/api/app/version")
backend\tests\test_health.py:34: response = await client.get("/docs")
backend\tests\test_health.py:43: response = await client.get("/metrics")
backend\tests\test_maintenance.py:10: response = await client.get("/api/app/maintenance")
backend\tests\test_maintenance.py:22: health = await client.get("/api/health/live")
backend\tests\test_maintenance.py:25: status = await client.get("/api/app/maintenance")
backend\tests\test_maintenance.py:29: blocked = await client.get("/api/products")
backend\tests\test_maintenance.py:32: assert body.get("code") == "MAINTENANCE_MODE"
backend\tests\test_maintenance.py:33: assert body.get("maintenance") is True
backend\tests\test_notifications_optimization.py:15: if (n.get("title") or "").startswith(PREFIX):
backend\tests\test_notifications_optimization.py:49: user_A_notifs = [n for n in user_A_notifs if (n.get("title") or "").startswith(PREFIX)]
backend\tests\test_notifications_optimization.py:55: low_stock_notifs = [n for n in low_stock_notifs if (n.get("title") or "").startswith(PREFIX)]
backend\tests\test_notifications_optimization.py:61: unread_notifs = [n for n in unread_notifs if (n.get("title") or "").startswith(PREFIX)]
backend\tests\test_notifications_optimization.py:81: test_notifs = [n for n in all_notifs if (n.get("title") or "").startswith(PREFIX)]
backend\tests\test_overall_optimization.py:112: resp = await client.get("/api/wishlist/", headers=headers)
backend\tests\test_overall_optimization.py:120: resp = await client.get("/api/cart/", headers=headers)
backend\tests\test_overall_optimization.py:128: resp = await client.get("/api/products/suggest?q=TEST_GEN_OPT", headers=headers)
backend\tests\test_products_filtering.py:16: response = await client.get("/api/products/")
backend\tests\test_products_filtering.py:20: response = await client.get("/api/products/?search=pen")
backend\tests\test_products_filtering.py:24: response = await client.get("/api/products/?category=stationery")
backend\tests\test_products_filtering.py:43: response = await client.get("/api/products/public?search=SprFuzyWdget")
backend\tests\test_recommendations.py:15: response = await client.get("/api/recommendations/")
backend\tests\test_referrals.py:24: response = await client.get("/api/referrals/settings")
backend\tests\test_referrals.py:69: response = await client.get("/api/referrals/settings")
backend\tests\test_referrals.py:110: eligibility_resp = await client.get("/api/referrals/check-eligibility", headers=user_auth)
backend\tests\test_referrals.py:126: ref_code = referrer.get("referralCode")
backend\tests\test_referrals.py:149: own_code = curr_user.get("referralCode")
backend\tests\test_referrals.py:155: scheme_resp = await client.get("/api/referrals/scheme", headers=user_auth)
backend\tests\test_referrals.py:177: for item in o.get("items", []):
backend\tests\test_referrals.py:178: pid = item.get("product") or item.get("productId")
backend\tests\test_referrals.py:208: eligibility_resp2 = await client.get("/api/referrals/check-eligibility", headers=user_auth)
backend\tests\test_router_pydantic_refactor.py:5: Category A dictionary .get( workarounds on request payloads/internal models.
backend\tests\test_router_pydantic_refactor.py:78: """AST visitor to detect Category A dictionary .get( workarounds.
backend\tests\test_router_pydantic_refactor.py:80: Category A: Disallowed .get( calls on request payloads, DB documents, or internal entities.
backend\tests\test_router_pydantic_refactor.py:105: # Exemption 3: Database repository singleton fetch methods (repo.get(), *_repository.get())
backend\tests\test_router_pydantic_refactor.py:174: """Parse a router file and return all Category A .get( violations."""
backend\tests\test_router_pydantic_refactor.py:196: # TIER 1: Static AST Analysis (Zero Category A .get( Calls)
backend\tests\test_router_pydantic_refactor.py:201: """Tier 1: AST / Static check verifying zero Category A .get( calls across routers."""
backend\tests\test_router_pydantic_refactor.py:217: """Verify that individual router module has zero Category A .get( dictionary workarounds."""
backend\tests\test_router_pydantic_refactor.py:223: f"  - L{lineno}: {caller}.get({args}) -> '{line}'" for lineno, caller, args, line in violations
backend\tests\test_router_pydantic_refactor.py:232: """Aggregate assertion verifying zero Category A .get( calls across the entire repository."""
backend\tests\test_router_pydantic_refactor.py:245: f"Found {total_violations_count} total Category A .get( calls across {len(all_violations)} files:"
backend\tests\test_router_pydantic_refactor.py:504: assert valid.payload.get("productId") == "prod_456"
backend\tests\test_router_pydantic_refactor.py:636: detail = res_empty.json().get("detail", [])
backend\tests\test_router_pydantic_refactor.py:638: assert any("type" in str(err.get("loc", [])) for err in detail)
backend\tests\test_router_pydantic_refactor.py:646: detail_missing = res_missing.json().get("detail", [])
backend\tests\test_router_pydantic_refactor.py:647: loc_fields = [err.get("loc", [])[-1] for err in detail_missing if err.get("loc")]
backend\tests\test_router_pydantic_refactor.py:658: # Endpoint accesses payload via dot-notation (never payload.get())
backend\tests\test_router_pydantic_refactor.py:669: assert data.get("status") == "ok"
backend\tests\test_router_pydantic_refactor.py:670: assert data.get("received_type") == "view"
backend\tests\test_wholesaler_dues.py:32: token = response.json().get("token", "")
backend\tests\test_wholesaler_dues.py:37: response = await client.get("/api/payments/dues", headers=headers)
backend\tests\test_wholesaler_dues.py:74: response = await client.get("/api/payments/dues", headers=headers)
backend\tests\test_wholesaler_dues.py:116: response = await client.get("/api/payments/dues", headers=headers)
backend\tests\test_wholesaler_dues.py:131: response = await client.get("/api/payments/dues", headers=headers)
backend\tests\test_wholesaler_dues.py:138: assert "pending dues" not in response.json().get("detail", "")
Extra\check_new_products.py:15: created = p.get("createdAt")
Extra\check_new_products_simple.py:19: created = p.get("createdAt")
Extra\check_new_products_simple.py:27: new_products.append(p.get("name"))
Extra\check_specific_products.py:18: name = p.get("name", "").lower()
Extra\check_specific_products.py:21: found[t].append(p.get("name"))
Extra\test_fast2sms_real.py:15: if ok and data.get('sent'):
`

## isinstance_dict (338 hits)
`
clean_bundle_dicts.py:8: 'bundle_specs = bundle.get("items", []) if isinstance(bundle, dict) else (bundle.items or [])',
clean_bundle_dicts.py:12: 'spec_qty = max(1, (spec.get("quantity", 1) if isinstance(spec, dict) else (spec.quantity if spec.quantity is not None else 1)))',
clean_bundle_dicts.py:16: 'spec_pid = str((spec.get("productId") if isinstance(spec, dict) else spec.productId) or "")',
clean_bundle_dicts.py:20: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))',
clean_orders.py:8: old_users = 'users_map = {str(u.get("id")) if isinstance(u, dict) else str(u.id): u for u in users_list}'
clean_orders.py:13: old_products = 'products_map = {str(p.get("id")) if isinstance(p, dict) else str(p.id): p for p in products_list}'
clean_orders.py:19: if isinstance(p, dict):
clean_payment_repo.py:9: # replace (p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None)) with getattr(p, "paymentId", getattr(p, "payment_id", None))
debug_payment.py:8: if isinstance(v, dict):
fix_address.py:9: return f'({var}.get("{attr}") if isinstance({var}, dict) else {var}.{attr})'
fix_all.py:95: if not any(isinstance(d, dict) and d.get("valetId") == valet_id_str for d in history):
fix_all.py:118: if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
fix_all.py:131: if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
fix_analytics.py:7: old_code = """        raw_dict = event.payload.root if hasattr(event.payload, "root") else (event.payload if isinstance(event.payload, dict) else {})
fix_analytics.py:10: new_code = """        raw_dict = event.payload.model_dump(exclude_unset=True) if hasattr(event.payload, 'model_dump') else (event.payload.root if hasattr(event.payload, "root") else (event.payload if isinstance(event.payload, dict) else {}))
fix_analytics.py:16: old_code_2 = """        raw_payload_dict = raw_payload.root if hasattr(raw_payload, "root") else (raw_payload if isinstance(raw_payload, dict) else {})
fix_analytics.py:19: new_code_2 = """        payload_obj = raw_payload if hasattr(raw_payload, "productId") else AnalyticsEventPayload(**(raw_payload.model_dump(exclude_unset=True) if hasattr(raw_payload, 'model_dump') else (raw_payload.root if hasattr(raw_payload, "root") else (raw_payload if isinstance(raw_payload, dict) else {}))))"""
fix_cust.py:10: 'if ("_id" not in data if isinstance(data, dict) else not getattr(data, "id", None)):\n            if isinstance(data, dict):\n                data["_id"] = str(uuid.uuid4())\n            else:\n                data.id = str(uuid.uuid4())',
fix_customer_segments.py:7: content = content.replace('data._id = str(uuid.uuid4())', 'if isinstance(data, dict):\n            data["_id"] = str(uuid.uuid4())\n        else:\n            data.id = str(uuid.uuid4())')
fix_delivery.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n        for slot in slots:',
fix_delivery_slots_ast.py:9: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])',
fix_delivery_slots_ast.py:10: 'slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])'
fix_delivery_slot_clean.py:10: 'slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n    for slot in slots:',
fix_delivery_slot_regex.py:11: r'\1slots = config.get("slots", []) if isinstance(config, dict) else getattr(config, "slots", [])\n\1for slot in slots:',
fix_del_charges.py:7: content = content.replace('charge = (result.charge) or 0.0', 'charge = (result["charge"] if isinstance(result, dict) and "charge" in result else (getattr(result, "charge", None) if not isinstance(result, dict) else None)) or 0.0')
fix_del_slots.py:11: return f'slot["{prop}"] if isinstance(slot, dict) and "{prop}" in slot else getattr(slot, "{prop}", None)'
fix_del_slots_all.py:11: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_all.py:17: if isinstance(s, dict):
fix_del_slots_clean.py:10: return s[p] if isinstance(s, dict) and p in s else (getattr(s, p, None) if not isinstance(s, dict) else None)
fix_del_slots_clean.py:25: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_manual.py:11: r'\1slots = config["slots"] if isinstance(config, dict) and "slots" in config else (getattr(config, "slots", []) if not isinstance(config, dict) else [])\n\1for slot in slots:',
fix_del_slots_manual.py:16: content = content.replace('slot.isActive', '(slot["isActive"] if isinstance(slot, dict) and "isActive" in slot else (getattr(slot, "isActive", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:17: content = content.replace('slot.isFullDay', '(slot["isFullDay"] if isinstance(slot, dict) and "isFullDay" in slot else (getattr(slot, "isFullDay", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:18: content = content.replace('slot.isUrgent', '(slot["isUrgent"] if isinstance(slot, dict) and "isUrgent" in slot else (getattr(slot, "isUrgent", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:19: content = content.replace('slot.startTime', '(slot["startTime"] if isinstance(slot, dict) and "startTime" in slot else (getattr(slot, "startTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:20: content = content.replace('slot.endTime', '(slot["endTime"] if isinstance(slot, dict) and "endTime" in slot else (getattr(slot, "endTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:21: content = content.replace('slot.cutoffTime', '(slot["cutoffTime"] if isinstance(slot, dict) and "cutoffTime" in slot else (getattr(slot, "cutoffTime", None) if not isinstance(slot, dict) else None))')
fix_del_slots_manual.py:24: content = content.replace('cap_val = slot.capacity', 'cap_val = (slot["capacity"] if isinstance(slot, dict) and "capacity" in slot else (getattr(slot, "capacity", None) if not isinstance(slot, dict) else None))')
fix_display_image.py:30: bundle_dict = bundle.model_dump() if hasattr(bundle, 'model_dump') else (bundle if isinstance(bundle, dict) else {})
fix_flat_daos.py:11: return match.group(0) + f'\n        if isinstance(data, dict):\n            data = {model_type}(**data)'
fix_flat_daos_update.py:11: return match.group(0) + f'\n        if isinstance(data, dict):\n            data = {model_type}(**data)'
fix_get.py:12: # qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)
fix_indent2.py:7: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n        product = await product_repository.findById(p_id)',
fix_indent2.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_indent2.py:11: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)',
fix_indent2.py:12: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
fix_indent_flat_base.py:7: if 'existing_dict = existing if isinstance(existing, dict)' in line:
fix_indent_flat_base.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_indent_order.py:7: if 'existing_dict = existing if isinstance(existing, dict)' in line:
fix_indent_order.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_indent_user.py:7: if 'existing_dict = existing if isinstance(existing, dict)' in line:
fix_indent_user.py:8: lines[i] = '        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n'
fix_lambda.py:7: content = content.replace('x["discount"]\n                    if isinstance(x, dict)\n                    else (x.discount if x.discount is not None else 0.0)', '(x.discount if x.discount is not None else 0.0)')
fix_notifs.py:7: content = content.replace('[u.id for u in unread_notifs]', '[u["_id"] if isinstance(u, dict) else u.id for u in unread_notifs]')
fix_notifs.py:8: content = content.replace('n["_id"]', 'n["_id"] if isinstance(n, dict) else n.id')
fix_orders_dict.py:17: if isinstance(p, dict):
fix_orders_dict.py:32: users_map = {str(u.get("id")) if isinstance(u, dict) else str(u.id): u for u in users_list}
fix_orders_dict.py:41: products_map = {str(p.get("id")) if isinstance(p, dict) else str(p.id): p for p in products_list}
fix_orders_import.py:13: order_resp = Order.model_validate(order, from_attributes=True) if not isinstance(order, dict) else Order.model_validate(order)
fix_orders_populate.py:9: order_resp = Order.model_validate(order, from_attributes=True) if not isinstance(order, dict) else Order.model_validate(order)
fix_orders_populate.py:37: if isinstance(obj, dict):
fix_orders_populate_pydantic.py:39: bad_validate = "Order.model_validate(order, from_attributes=True) if not isinstance(order, dict) else Order.model_validate(order)"
fix_orders_regex.py:10: #                 if isinstance(validation_raw, dict)
fix_orders_regex2.py:8: # Replace ANY `.model_validate(var) if isinstance(var, dict) else (var if ... else ...)`
fix_order_dao.py:15: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_payment_in.py:14: if isinstance(query["{key}"], dict) and "$in" in query["{key}"]:
fix_payment_repo2.py:9: if isinstance(e, dict):
fix_payment_repo3.py:31: if isinstance(e, dict):
fix_product_in.py:14: if isinstance(val, dict) and "$in" in val:
fix_repo_return.py:14: text = text.replace('return sorted(notifications, key=lambda x: x.createdAt or "", reverse=True)', 'sorted_notifs = sorted(notifications, key=lambda x: x.createdAt or "", reverse=True)\n        return [NotificationInternal(**n) if isinstance(n, dict) else NotificationInternal.model_validate(n, from_attributes=True) for n in sorted_notifs]')
fix_repo_return.py:18: text = text.replace('return await self.storage.findById(id)', 'result = await self.storage.findById(id)\n        if not result: return None\n        return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)')
fix_repo_return.py:22: text = text.replace('return await self.storage.create(notification_data)', 'result = await self.storage.create(notification_data)\n        return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)')
fix_repo_return.py:25: text = text.replace('return await self.storage.update(id, update_data)', 'result = await self.storage.update(id, update_data)\n        return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)')
fix_segment.py:23: if (isinstance(data, dict) and data.get(k) is not None) or (not isinstance(data, dict) and getattr(data, k, None) is not None):
fix_segment.py:24: filters[k] = data.pop(k) if isinstance(data, dict) else getattr(data, k)
fix_segment.py:25: if not isinstance(data, dict): setattr(data, k, None)
fix_segment.py:27: if not isinstance(data, dict):
fix_segment.py:36: if isinstance(data, dict):
fix_sort.py:8: new_code = 'enriched.sort(key=lambda x: (x.get("salesCount", x.get("sales_count")) if x.get("salesCount", x.get("sales_count")) is not None else 0) if isinstance(x, dict) else (x.sales_count if x.sales_count is not None else 0), reverse=True)'
fix_sort2.py:7: old_code = 'enriched.sort(key=lambda x: (x.get("salesCount", x.get("sales_count")) if x.get("salesCount", x.get("sales_count")) is not None else 0) if isinstance(x, dict) else (x.sales_count if x.sales_count is not None else 0), reverse=True)'
fix_sort2.py:8: new_code = 'enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else x.get("sales_count", 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)'
fix_sort2.py:9: new_code2 = 'enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else (x["sales_count"] if "sales_count" in x else 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)'
fix_user.py:8: content = content.replace('if update_data.email is not None:', 'email_val = update_data.get("email") if isinstance(update_data, dict) else getattr(update_data, "email", None)\n        if email_val is not None:')
fix_user.py:16: content = content.replace('otp_val = payload.otp', 'otp_val = payload.get("otp") if isinstance(payload, dict) else getattr(payload, "otp", None)')
fix_user_create.py:8: '''        if isinstance(user_data, dict):
fix_user_create.py:10: '''        if isinstance(user_data, dict):
fix_user_dao2.py:14: # payment_terms = (update_data.get("paymentTerms") if isinstance(update_data, dict) else update_data.payment_terms)
fix_user_dao2.py:19: if isinstance(obj, dict):
fix_user_dao3.py:14: content = content.replace("update_data.paymentTerms", "(update_data.get('paymentTerms', update_data.get('payment_terms')) if isinstance(update_data, dict) else getattr(update_data, 'payment_terms', getattr(update_data, 'paymentTerms', None)))")
fix_user_dao3.py:15: content = content.replace("update_data.creditLimit", "(update_data.get('creditLimit', update_data.get('credit_limit')) if isinstance(update_data, dict) else getattr(update_data, 'credit_limit', getattr(update_data, 'creditLimit', None)))")
fix_user_dao3.py:16: content = content.replace("update_data.creditUsed", "(update_data.get('creditUsed', update_data.get('credit_used')) if isinstance(update_data, dict) else getattr(update_data, 'credit_used', getattr(update_data, 'creditUsed', None)))")
fix_user_dao3.py:17: content = content.replace("update_data.approvalStatus", "(update_data.get('approvalStatus', update_data.get('approval_status')) if isinstance(update_data, dict) else getattr(update_data, 'approval_status', getattr(update_data, 'approvalStatus', None)))")
fix_user_dao4.py:8: content = content.replace("update_data.assignedSalesperson", "(update_data.get('assignedSalesperson', update_data.get('assigned_salesperson')) if isinstance(update_data, dict) else getattr(update_data, 'assigned_salesperson', getattr(update_data, 'assignedSalesperson', None)))")
fix_user_dao_final.py:27: return f"(update_data.get('{camel}', update_data.get('{snake}')) if isinstance(update_data, dict) else getattr(update_data, '{snake}', getattr(update_data, '{camel}', None)))"
fix_user_in.py:13: if isinstance(val, dict) and "$in" in val:
fix_user_in.py:37: if isinstance(v, dict) and "$in" in v:
fix_user_repo.py:9: email_val = update_data.get("email") if isinstance(update_data, dict) else update_data.email
fix_user_repo.py:17: phone_val = update_data.get("phone") if isinstance(update_data, dict) else update_data.phone
fix_user_repo.py:25: if isinstance(update_data, dict): update_data["password"] = get_password_hash(update_data["password"])
fix_user_repo.py:52: return UserResponse.model_validate(created_dict) if isinstance(created_dict, dict) else created_dict'''
fix_user_repo_update.py:9: lines.insert(i+1, '        if isinstance(update_data, dict):\n            update_data = type("UpdateObj", (), update_data)()\n')
fix_user_repo_update2.py:8: content = content.replace('update_data.password = get_password_hash(update_data.password)', 'if isinstance(update_data, dict): update_data["password"] = get_password_hash(update_data["password"])\n            else: update_data.password = get_password_hash(update_data.password)')
fix_user_repo_update3.py:7: content = content.replace('        if isinstance(update_data, dict):\n            update_data = type("UpdateObj", (), update_data)()\n', '')
patch_bundle_repo.py:8: 'if any(getattr(i, "productId", i.get("productId", i.get("product_id")) if isinstance(i, dict) else getattr(i, "product_id", None)) == product_id for i in items):'
patch_flat_base_dao.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_flat_base_dao.py:7: if isinstance(update_data, dict):
patch_flat_base_dao.py:14: 'existing_dict = existing if isinstance(existing, dict) else existing.__dict__\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_flat_base_dao2.py:8: replacement = '''existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_flat_base_dao2.py:9: if isinstance(update_data, dict):
patch_mysql_flat_base_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else existing.__dict__\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_mysql_order_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_mysql_order_dao_update.py:9: return f'(update_data.get("{attr}") if isinstance(update_data, dict) else update_data.{attr})'
patch_mysql_user_dao.py:8: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
patch_orders4.py:8: 'bundle_specs = bundle.get("items", []) if isinstance(bundle, dict) else (bundle.items or [])'
patch_orders4.py:12: 'spec_qty = max(1, (spec.get("quantity", 1) if isinstance(spec, dict) else (spec.quantity if spec.quantity is not None else 1)))'
patch_orders4.py:16: 'spec_pid = str((spec.get("productId") if isinstance(spec, dict) else spec.productId) or "")'
patch_orders5.py:8: 'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))\n                    new_sales = (sales_c if sales_c is not None else 0) + copies'
patch_order_clean.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_order_clean.py:10: if isinstance(update_data, dict):
patch_order_dao_update2.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_order_dao_update2.py:7: if isinstance(update_data, dict):
patch_order_dao_update2.py:14: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_order_fields.py:8: '        if isinstance(update_data, dict):\n            return await self.storage.update(id, update_data)\n        fields = {}\n        for f in getattr(update_data, "model_fields_set", []):'
patch_order_repo.py:8: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "out_for_delivery"'
patch_order_repo.py:12: '(update_data.get("shippedAt") if isinstance(update_data, dict) else update_data.shippedAt) is None'
patch_order_repo.py:16: 'if isinstance(update_data, dict): update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()\n        else: update_data.shippedAt = datetime.now(timezone.utc).isoformat()'
patch_order_repo.py:21: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "delivered"'
patch_order_repo.py:25: '(update_data.get("deliveredAt") if isinstance(update_data, dict) else update_data.deliveredAt) is None'
patch_order_repo.py:29: 'if isinstance(update_data, dict): update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()\n            else: update_data.deliveredAt = datetime.now(timezone.utc).isoformat()'
patch_order_repo.py:33: '(update_data.get("paymentStatus") if isinstance(update_data, dict) else update_data.paymentStatus) is None'
patch_order_repo.py:37: 'if isinstance(update_data, dict): update_data["paymentStatus"] = "paid"\n                    else: update_data.paymentStatus = "paid"'
patch_order_repo_fixed.py:9: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_fixed.py:12: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_fixed.py:14: if isinstance(update_data, dict):
patch_order_repo_fixed.py:20: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_fixed.py:22: if isinstance(update_data, dict):
patch_order_repo_fixed.py:29: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_order_repo_fixed.py:31: if isinstance(update_data, dict):
patch_order_repo_replace.py:12: '(update_data.get("status") if isinstance(update_data, dict) else update_data.status)'
patch_order_repo_replace.py:16: '(update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)) is None'
patch_order_repo_replace.py:20: 'if isinstance(update_data, dict): update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()\n        elif not isinstance(update_data, dict): update_data.shippedAt = '
patch_order_repo_replace.py:24: '(update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)) is None'
patch_order_repo_replace.py:28: 'if isinstance(update_data, dict): update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()\n            elif not isinstance(update_data, dict): update_data.deliveredAt = '
patch_order_repo_replace.py:32: '(update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)) is None'
patch_order_repo_replace.py:36: 'if isinstance(update_data, dict): update_data["paymentStatus"] = "paid"\n                    elif not isinstance(update_data, dict): update_data.paymentStatus = '
patch_order_repo_replace.py:40: '(update_data.get("codPaymentReceived") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceived", None)) is None'
patch_order_repo_replace.py:44: 'if isinstance(update_data, dict): update_data["codPaymentReceived"] = True\n                elif not isinstance(update_data, dict): update_data.codPaymentReceived = '
patch_order_repo_replace.py:48: '(update_data.get("codPaymentReceivedAt") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceivedAt", None)) is None'
patch_order_repo_replace.py:52: 'if isinstance(update_data, dict): update_data["codPaymentReceivedAt"] = datetime.now(timezone.utc).isoformat()\n                elif not isinstance(update_data, dict): update_data.codPaymentReceivedAt = '
patch_order_repo_replace.py:56: 'if isinstance(update_data, dict): update_data["turnaroundHours"] = round(hours, 2)\n                    elif not isinstance(update_data, dict): update_data.turnaroundHours = '
patch_order_repo_replace.py:60: '(update_data.get("cancelledAt") if isinstance(update_data, dict) else getattr(update_data, "cancelledAt", None)) is None'
patch_order_repo_replace.py:64: 'if isinstance(update_data, dict): update_data["cancelledAt"] = datetime.now(timezone.utc).isoformat()\n        elif not isinstance(update_data, dict): update_data.cancelledAt = '
patch_order_repo_replace.py:69: 'datetime.fromisoformat((update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt"))'
patch_order_repo_rewrite.py:10: status = update_data.get("status") if isinstance(update_data, dict) else getattr(update_data, "status", None)
patch_order_repo_rewrite.py:13: shipped_at = update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)
patch_order_repo_rewrite.py:15: if isinstance(update_data, dict):
patch_order_repo_rewrite.py:21: delivered_at = update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)
patch_order_repo_rewrite.py:23: if isinstance(update_data, dict):
patch_order_repo_rewrite.py:30: payment_status = update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)
patch_order_repo_rewrite.py:32: if isinstance(update_data, dict):
patch_payment.py:8: '(p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None))'
patch_payment_in.py:10: if isinstance(query["orderId"], dict) and "" in query["orderId"]:
patch_product_repo_fix.py:10: if isinstance(product_data, dict):
patch_routers_bundles.py:9: 'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)'
patch_routers_bundles.py:13: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem('
patch_routers_bundles3.py:8: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)'
patch_routers_bundles_pid.py:7: 'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)',
patch_routers_bundles_pid.py:8: 'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
patch_routers_bundles_pid.py:24: 'available < (item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1))'
patch_routers_bundles_pid.py:28: 'required: {item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)}'
patch_routers_bundles_pid.py:32: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))'
patch_routers_bundles_pid.py:36: 'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)'
patch_routers_bundles_pid.py:39: 'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem(',
patch_stock_dao.py:10: res = res.replace('data.productId', 'data.get("productId") if isinstance(data, dict) else getattr(data, "productId", None)')
patch_stock_dao.py:11: res = res.replace('data.userId', 'data.get("userId") if isinstance(data, dict) else getattr(data, "userId", None)')
patch_stock_dao.py:12: res = res.replace('data.quantity', 'data.get("quantity") if isinstance(data, dict) else getattr(data, "quantity", None)')
patch_stock_dao.py:13: res = res.replace('data.status', 'data.get("status") if isinstance(data, dict) else getattr(data, "status", None)')
patch_stock_dao.py:14: res = res.replace('data.expiresAt', 'data.get("expiresAt") if isinstance(data, dict) else getattr(data, "expiresAt", None)')
patch_stock_dao.py:15: res = res.replace('if "expiresAt" in data:', 'if (isinstance(data, dict) and "expiresAt" in data) or hasattr(data, "expiresAt"):')
patch_stock_reservations_dao.py:13: existing_dict = existing if isinstance(existing, dict) else existing.__dict__
patch_stock_reservations_dao.py:14: data_dict = data if isinstance(data, dict) else getattr(data, '__dict__', {})
patch_user_careful.py:16: lines[i] = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_careful.py:17: if isinstance(update_data, dict):
patch_user_careful.py:48: lines[i] = '    async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n'
patch_user_children_both.py:12: # Insert data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})
patch_user_children_both.py:13: rep_block = rep_block.replace('async def _replace_children(self, session, uid: int, data: Dict):\n', 'async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n')
patch_user_clean.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_clean.py:10: if isinstance(update_data, dict):
patch_user_dao_update.py:6: replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_dao_update.py:7: if isinstance(update_data, dict):
patch_user_dao_update.py:14: 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
patch_user_final.py:9: replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
patch_user_final.py:10: if isinstance(update_data, dict):
patch_user_repo_return.py:10: return UserResponse.model_validate(created_dict) if isinstance(created_dict, dict) else created_dict'''
patch_zone.py:8: 'if pincode in (zone.get("pincodes", []) if isinstance(zone, dict) else (getattr(zone, "pincodes", []) or [])):'
patch_zone.py:12: '_active_seller_cache[zone.get("id") if isinstance(zone, dict) else zone.id] = list(active)'
rewrite_brand_repo.py:8: name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_brand_repo.py:9: description=getattr(data, 'description', data.get('description') if isinstance(data, dict) else None),
rewrite_brand_repo.py:10: isActive=getattr(data, 'isActive', data.get('isActive') if isinstance(data, dict) else True)
rewrite_brand_repo.py:18: if isinstance(update_data, dict):
rewrite_repos.py:41: # if isinstance(data, dict):
rewrite_repos.py:60: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos.py:79: replacement += f"        if isinstance({var_in}, dict):\n"
rewrite_repos2.py:50: mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos2.py:75: replacement += f"            if isinstance({var_in}, dict):\n"
rewrite_repos3.py:49: mapping.append(f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
rewrite_repos3.py:74: replacement += f"{indent}    if isinstance({var_in}, dict):\n"
rewrite_repos4.py:44: #                name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
rewrite_repos4.py:58: replacement = f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos4.py:71: #            if isinstance(data, dict):
rewrite_repos4.py:85: replacement = f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual.py:23: res += f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual.py:43: content = content.replace('        return await self.storage.update(id, UserInternalUpdate(**update_data) if isinstance(update_data, dict) else update_data)',
rewrite_repos_manual_2.py:23: res += f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual_2.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_3.py:23: res += f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual_3.py:35: res += f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None),\n"
rewrite_repos_manual_4.py:23: res += f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual_4.py:34: content = content.replace('        return await self.storage.update(id, UserInternalUpdate(**update_data) if isinstance(update_data, dict) else update_data)', f'{update_block}\n        return await self.storage.update(id, internal_update)')
rewrite_repos_manual_5.py:23: res += f"{indent}if isinstance({var_in}, dict):\n"
rewrite_repos_manual_5.py:37: if isinstance(update_data, dict):
rewrite_repos_model_validate.py:9: # if isinstance(data, dict):
backend\fix_base_dao.py:25: out.append('        if isinstance(data, dict):\n')
backend\fix_base_dao.py:97: out.append('        if isinstance(update_data, dict):\n')
backend\fix_base_dao_clean.py:23: if isinstance(update_data, dict):
backend\fix_base_dao_clean.py:56: if isinstance(update_data, dict):
backend\fix_mysql_order_dao.py:9: if 'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})' in line:
backend\fix_remove_update_dict.py:13: if 'if isinstance(update_data, dict):' in line:
backend\fix_stock_update.py:7: if 'existing_dict = existing if isinstance(existing, dict) else existing.__dict__' in line:
backend\scratch_add_sellers_dao.py:18: s_id = seller.get("sellerId") if isinstance(seller, dict) else seller.sellerId
backend\scratch_add_sellers_dao.py:19: s_stock = seller.get("stock", 0) if isinstance(seller, dict) else seller.stock
backend\scratch_add_sellers_dao.py:20: s_active = seller.get("isActive", False) if isinstance(seller, dict) else seller.isActive
backend\scratch_add_sellers_dao.py:21: s_status = seller.get("requestStatus", "pending") if isinstance(seller, dict) else seller.requestStatus
backend\scratch_fix_analytics_events.py:20: if event.payload and isinstance(event.payload, dict):
backend\scratch_fix_gets.py:7: 'c_name = child.get("name") if isinstance(child, dict) else child.name',
backend\scratch_fix_gets.py:17: 'ticket.get("user_id") if isinstance(ticket, dict) else getattr(ticket, "user_id", None)',
backend\scratch_fix_gets.py:21: 'ticket.get("userId") if isinstance(ticket, dict) else getattr(ticket, "userId", None)',
backend\scratch_fix_gets.py:25: 'ticket.get("name") if isinstance(ticket, dict) else ticket.name',
backend\scratch_fix_gets.py:29: 'ticket.get("email") if isinstance(ticket, dict) else ticket.email',
backend\scratch_fix_gets.py:33: 'str(ticket.get("id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "id", ""))',
backend\scratch_fix_gets.py:37: 'str(ticket.get("_id", "")) if isinstance(ticket, dict) else str(getattr(ticket, "_id", ""))',
backend\scratch_fix_gets.py:47: 'raw_items = wishlist.get("items", []) if isinstance(wishlist, dict) else (wishlist.items or [])',
backend\scratch_fix_gets.py:51: 'item.get("product") if isinstance(item, dict) else item.product',
backend\scratch_fix_gets.py:55: 'item.get("quantity", 1) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)',
backend\scratch_fix_gets2.py:6: '''cat_dict["gst"] = (cat.gst if hasattr(cat, 'gst') and cat.gst is not None else 0) if not isinstance(cat, dict) else (cat.get("gst", 0))''',
backend\scratch_fix_gets2.py:15: 't_user = ticket.get("user") if isinstance(ticket, dict) else ticket.user',
backend\scratch_fix_gets2.py:19: 't_assigned_to = ticket.get("assignedTo") if isinstance(ticket, dict) else ticket.assignedTo',
backend\scratch_fix_gets2.py:23: 't_responses = ticket.get("responses") if isinstance(ticket, dict) else ticket.responses',
backend\scratch_fix_record_event.py:8: if event.payload and isinstance(event.payload, dict):
backend\scratch_fix_record_event.py:13: items_to_iter = event.payload.items() if isinstance(event.payload, dict) else event.payload
backend\scratch_patch_orders.py:10: 'seller_ids_in_order = {item.get("sellerId") for item in order_items if isinstance(item, dict) and item.get("sellerId")}'
backend\scratch_patch_orders.py:15: '{item.get("sellerId") for item in order_items if isinstance(item, dict) and item.get("sellerId")}'
backend\app\main.py:497: if isinstance(e, HTTPException) and isinstance(e.detail, dict) and (e.detail["code"] if "code" in e.detail else None) == ERR_SESSION_REVOKED:
backend\app\db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
backend\app\db\mysql_flat_base_dao.py:240: if isinstance(update_data, dict):
backend\app\db\mysql_flat_daos.py:76: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:103: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:221: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:272: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:385: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:416: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:553: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:620: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:764: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:811: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:928: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:963: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1073: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1112: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1224: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1403: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1446: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1568: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1611: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1720: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1751: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1860: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:1899: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2014: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2053: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2168: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2207: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2326: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2369: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2487: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2526: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2645: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2688: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2798: if isinstance(data, dict):
backend\app\db\mysql_flat_daos.py:2829: if isinstance(data, dict):
backend\app\db\mysql_generated_daos.py:113: if isinstance(data, dict):
backend\app\db\mysql_generated_daos.py:136: if isinstance(item, dict):
backend\app\db\mysql_generated_daos.py:178: if isinstance(data, dict):
backend\app\db\mysql_generated_daos.py:203: existing_dict = existing if isinstance(existing, dict) else existing.__dict__
backend\app\db\mysql_generated_daos.py:204: data_dict = data if isinstance(data, dict) else data.__dict__
backend\app\db\mysql_seller_availability_dao.py:87: if isinstance(v, dict) and "$in" in v:
backend\app\db\mysql_sub_order_dao.py:194: if isinstance(v, dict):
backend\app\db\mysql_wishlist_dao.py:54: pid = item.product if isinstance(item, dict) else item
backend\app\jobs\valet_timeout_job.py:99: if isinstance(entry, dict):
backend\app\jobs\valet_timeout_job.py:194: if isinstance(entry, dict):
backend\app\jobs\valet_timeout_job.py:314: if not any((isinstance(d, dict) and (d['valetId'] if 'valetId' in d else None) == pending_valet_id for d in history)):
backend\app\jobs\valet_timeout_job.py:338: if not any((isinstance(d, dict) and (d['valetId'] if 'valetId' in d else None) == pending_valet_id for d in history)):
backend\app\repositories\activity_repository.py:31: if device and isinstance(device, dict):
backend\app\repositories\notification_repository.py:51: return [NotificationInternal(**n) if isinstance(n, dict) else NotificationInternal.model_validate(n, from_attributes=True) for n in sorted_notifs]
backend\app\repositories\notification_repository.py:56: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
backend\app\repositories\notification_repository.py:64: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
backend\app\repositories\notification_repository.py:69: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
backend\app\repositories\payment_repository.py:102: if isinstance(update_data, dict):
backend\app\repositories\payment_repository.py:177: if isinstance(e, dict):
backend\app\repositories\payment_repository.py:241: if isinstance(e, dict):
backend\app\repositories\product_repository.py:938: if isinstance(product_data, dict):
backend\app\repositories\recommendation_repository.py:1050: sub_cat = sc["name"] if "name" in sc else None if isinstance(sc, dict) else sc
backend\app\routers\auth.py:411: claims = RefreshTokenClaims(**data) if isinstance(data, dict) else data
backend\app\routers\commission.py:279: if isinstance(updated, dict):
backend\app\routers\delivery_charges.py:376: # and then checked isinstance(update_dict, dict) which was always False, so
backend\app\routers\delivery_slots.py:114: zone_id = zone_data.id or (zone_data["_id"] if isinstance(zone_data, dict) and "_id" in zone_data else zone_data["id"] if isinstance(zone_data, dict) and "id" in zone_data else None) if zone_data else None
backend\app\routers\products.py:718: f = ProductFacets(**facets) if isinstance(facets, dict) else (facets if isinstance(facets, ProductFacets) else ProductFacets())
backend\app\routers\products.py:874: f = ProductFacets(**facets) if isinstance(facets, dict) else (facets if isinstance(facets, ProductFacets) else ProductFacets())
backend\app\routers\push_notifications.py:313: request.subscription["endpoint"] if isinstance(request.subscription, dict) and "endpoint" in request.subscription else None
backend\app\routers\recommendations.py:367: section_weights = (section_wise[body.slot] if isinstance(section_wise, dict) and body.slot in section_wise else None) or engagement or {}
backend\app\routers\recommendations.py:369: weight = section_weights["add_to_cart"] if isinstance(section_weights, dict) and "add_to_cart" in section_weights else 3
backend\app\routers\recommendations.py:371: weight = section_weights["product_view"] if isinstance(section_weights, dict) and "product_view" in section_weights else 1
backend\app\routers\valet_availability.py:225: enriched.sort(key=lambda d: d.date if not isinstance(d, dict) else (d["date"] if "date" in d and d["date"] is not None else ""))
backend\app\routers\wishlist.py:55: if isinstance(it, dict):
backend\app\utils\email_otp.py:126: if not isinstance((record["devices"] if "devices" in record else None), dict):
backend\app\utils\otp.py:133: if isinstance(value, dict):
backend\app\utils\otp.py:289: if not isinstance((record["devices"] if "devices" in record else None), dict):
backend\app\utils\otp.py:437: if not user_record or not isinstance((user_record["devices"] if "devices" in user_record else None), dict):
backend\scratch\clean_all.py:28: # Pattern: X["Y"] if isinstance(X, dict) else (getattr(X, "Y", 0)) -> X.Y
backend\scratch\clean_orders.py:7: # Pattern: X["Y"] if isinstance(X, dict) and "Y" in X else getattr(X, "Y", default)
backend\scratch\clean_orders.py:11: # Pattern: getattr(X, "Y", None) or (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
backend\scratch\clean_orders.py:14: # Pattern: getattr(X, "Y", None) if hasattr(X, "Y") else (X["Y"] if isinstance(X, dict) and "Y" in X else ...)
backend\scripts\backfill_product_sellers.py:44: if not isinstance(s, dict):
backend\scripts\test_e2e_logic.py:23: print(f"OK GET /pincodes. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} records.")
backend\scripts\test_e2e_logic.py:41: print(f"OK GET /delivery-charges. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} records.")
backend\scripts\test_e2e_logic.py:58: print(f"OK GET /delivery-slots. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} configs.")
backend\tests\test_router_pydantic_refactor.py:319: assert isinstance(openapi_schema, dict), "OpenAPI schema must be a dictionary"
`

## model_dump (63 hits)
`
fix.py:111: # .model_dump()
fix.py:113: new_content = new_content.replace('.model_dump()', '.__dict__')
fix_analytics.py:10: new_code = """        raw_dict = event.payload.model_dump(exclude_unset=True) if hasattr(event.payload, 'model_dump') else (event.payload.root if hasattr(event.payload, "root") else (event.payload if isinstance(event.payload, dict) else {}))
fix_analytics.py:19: new_code_2 = """        payload_obj = raw_payload if hasattr(raw_payload, "productId") else AnalyticsEventPayload(**(raw_payload.model_dump(exclude_unset=True) if hasattr(raw_payload, 'model_dump') else (raw_payload.root if hasattr(raw_payload, "root") else (raw_payload if isinstance(raw_payload, dict) else {}))))"""
fix_collections2.py:22: response_dict = collection.model_dump(by_alias=True)
fix_daos2.py:6: # Revert b	merged = ...(**{**existing, **data}) back to existing.model_dump()
fix_daos2.py:7: content = re.sub(r'\(\**\{\**existing, \**data\}\)', r'(**{0z**existing.model_dump(by_alias=True), **data.model_dump(exclude_unset=True)})', content)
fix_daos3.py:4: c = re.sub(r'merged = \w+InternalUpdate\(\**\{\**existing\.model_dump\(by_alias=True\), \**data\.model_dump\(exclude_unset=True\)\}\)', 'merged = {**existing.model_dump(by_alias=True), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)}', c)
fix_data_dump.py:6: content = content.replace('**data}', '**data.model_dump(exclude_unset=True)}')
fix_display_image.py:30: bundle_dict = bundle.model_dump() if hasattr(bundle, 'model_dump') else (bundle if isinstance(bundle, dict) else {})
fix_dump.py:7: content = content.replace("bundle.model_dump()", "bundle.model_dump(by_alias=True)")
fix_model_dump.py:7: text = text.replace('subscription.model_dump()', 'json.loads(subscription.model_dump_json())')
fix_push.py:15: text = text.replace('sub_payload = request.subscription.model_dump() if has_web_subscription and request.subscription else None', 'sub_payload = request.subscription if has_web_subscription and request.subscription else None')
fix_push2.py:7: text = text.replace('sub_payload = request.subscription.model_dump() if has_web_subscription and request.subscription else None', 'sub_payload = request.subscription if has_web_subscription and request.subscription else None')
fix_tests_bugs.py:41: c = c.replace('doc = {k: v for k, v in settings[0].items()}', 'doc = {k: v for k, v in settings[0].model_dump().items()} if hasattr(settings[0], "model_dump") else {k: v for k, v in settings[0].items()}')
patch_cat_dao.py:9: 'existing_dict = existing.model_dump(by_alias=True)'
patch_cat_dao.py:13: 'update_dict = update_data.model_dump(exclude_unset=True)'
rewrite_repos.py:44: #     internal_data = BrandInternalCreate(**data.model_dump(exclude_unset=True))
rewrite_repos4.py:88: replacement += f"{indent}    {var_out} = {model_name}.model_validate({var_in}.model_dump(exclude_unset=True))"
rewrite_repos_model_validate.py:12: #     internal_data = BrandInternalCreate(**data.model_dump(exclude_unset=True))
rewrite_repos_model_validate.py:15: # and Model(**obj.model_dump(...)) with Model.model_validate(obj.model_dump(...))
rewrite_returns.py:19: item_dict = item.model_dump()
rewrite_returns.py:20: prod_dict = product.model_dump() if product else {"_id": pid, "name": "Product not found"}
rewrite_returns.py:24: base_dict = request.model_dump(by_alias=True)
test_pydantic.py:17: b2 = B.model_validate(a.model_dump())
backend\scratch_append.py:45: update_data = {"sellers": [s.model_dump() for s in sellers_list]}
backend\scratch_append.py:79: update_data = {"sellers": [s.model_dump() for s in sellers_list]}
backend\scratch_append.py:135: update_data = {"sellers": [s.model_dump() for s in sellers_list]}
backend\scratch_fix_all_gets.py:18: # Wait, user said no getattr! I will use \1.__dict__.get(\2, \3)? But it's Pydantic, so \1.model_dump().get(\2, \3)?
backend\scratch_fix_analytics_events.py:10: old_code = '''    enriched_event = event.model_dump()
backend\scratch_fix_session.py:7: '''existing_dict = existing.model_dump(exclude_unset=True) if hasattr(existing, 'model_dump') else dict(existing)''',
backend\scratch_fix_session.py:8: '''existing_dict = existing.model_dump(exclude_unset=True, by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)'''
backend\scratch_fix_session.py:12: '''update_dict = update_data.model_dump(exclude_unset=True)''',
backend\scratch_fix_session.py:13: '''update_dict = update_data.model_dump(exclude_unset=True, by_alias=True)'''
backend\scratch_patch_auth_dump.py:8: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_auth_mode.py:5: c = c.replace('user.model_dump(by_alias=True)', 'user.model_dump(by_alias=True, mode="json")')
backend\scratch_patch_auth_unpack.py:8: 'user_response_dict = {**current_user.model_dump(by_alias=True), "effectiveRole": effective_role}'
backend\scratch_patch_categories_responses.py:8: c = c.replace('return result', 'return result.model_dump(by_alias=True, mode="json") if hasattr(result, "model_dump") else result')
backend\scratch_patch_categories_responses.py:9: c = c.replace('return created', 'return created.model_dump(by_alias=True, mode="json") if hasattr(created, "model_dump") else created')
backend\scratch_patch_categories_responses.py:10: c = c.replace('return updated', 'return updated.model_dump(by_alias=True, mode="json") if hasattr(updated, "model_dump") else updated')
backend\scratch_patch_categories_responses.py:11: c = c.replace('return category', 'return category.model_dump(by_alias=True, mode="json") if hasattr(category, "model_dump") else category')
backend\scratch_patch_daos.py:11: r'{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else dict(existing)), **\1}',
backend\scratch_patch_routers_dump.py:18: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_routers_dump_safe.py:18: return f"**({var_name}.model_dump(by_alias=True, mode='json') if hasattr({var_name}, 'model_dump') else {var_name})"
backend\scratch_patch_slots_dict.py:40: c = c.replace('slot.get("dict")()', 'slot.model_dump() if hasattr(slot, "model_dump") else slot.dict() if hasattr(slot, "dict") else slot')
backend\scratch_patch_update_session.py:10: existing_dict = existing.model_dump(by_alias=True) if hasattr(existing, 'model_dump') else dict(existing)
backend\scratch_patch_users_model_dump.py:5: c = c.replace('user_data.dict(exclude_unset=True)', 'user_data.model_dump(exclude_unset=True, by_alias=True)')
backend\scratch_patch_user_mapping.py:8: 'return UserResponse(**user.model_dump(by_alias=True, mode="json"))'
backend\scratch_patch_valet_availability_dates.py:8: c = c.replace('return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.isoformat() if hasattr(doc.date, "isoformat") else doc.date) in upcoming_dates]', 'return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.strftime("%Y-%m-%d") if hasattr(doc.date, "strftime") else str(doc.date)[:10]) in upcoming_dates]')
backend\scratch_patch_valet_availability_responses.py:7: c = c.replace('return created', 'return created.model_dump(by_alias=True, mode="json") if hasattr(created, "model_dump") else created')
backend\scratch_patch_valet_availability_responses.py:8: c = c.replace('return [doc for doc in all_docs if doc.date in upcoming_dates]', 'return [(doc.model_dump(by_alias=True, mode="json") if hasattr(doc, "model_dump") else doc) for doc in all_docs if (doc.date.isoformat() if hasattr(doc.date, "isoformat") else doc.date) in upcoming_dates]')
backend\scratch_patch_valet_availability_responses.py:9: c = c.replace('return enriched', 'return [(e.model_dump(by_alias=True, mode="json") if hasattr(e, "model_dump") else e) for e in enriched] if enriched and hasattr(enriched[0], "model_dump") else enriched')
backend\scratch_test_db_user.py:17: print("User Model:", user_model.model_dump() if user_model else "None")
backend\scratch_test_db_user_2.py:17: print("All fields:", u.model_dump())
backend\scratch_wait.py:11: # We want to replace `return var` with `return var.model_dump(...)` for known vars.
backend\scratch\clean_all.py:9: # Becomes: **user.model_dump(by_alias=True)
backend\scratch\clean_all.py:10: content = re.sub(r'\*\*\(\s*(\w+)\s*if\s*hasattr\(\1,\s*[\'"]model_dump[\'"]\)\s*else\s*\1\s*\)', r'**\1.model_dump(by_alias=True)', content)
backend\scratch\clean_hasattr_final.py:11: content = re.sub(r'(\w+)\.model_dump\(([^)]*)\)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*dict\(\1\)', r'\1.model_dump(\2)', content)
backend\scratch\clean_hasattr_final.py:13: content = re.sub(r'(\w+)\.model_dump\(\)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*dict\(\1\)', r'\1.model_dump()', content)
backend\scratch\clean_hasattr_final.py:17: content = content.replace('sub_payload = request.subscription.model_dump() if (has_web_subscription and hasattr(request.subscription, "model_dump")) else (request.subscription if has_web_subscription else None)', 'sub_payload = request.subscription.model_dump() if has_web_subscription else None')
backend\scratch\clean_hasattr_final.py:27: content = content.replace('[p.model_dump(by_alias=True) if hasattr(p, "model_dump") else p for p in payment_entries]', '[p.model_dump(by_alias=True) for p in payment_entries]')
backend\scratch\clean_hasattr_final.py:28: content = content.replace('product.model_dump(by_alias=True) if product and hasattr(product, "model_dump") else (product if product else {"_id": prod_id, "name": "Product not found"})', 'product.model_dump(by_alias=True) if product else {"_id": prod_id, "name": "Product not found"}')
backend\tests\test_router_pydantic_refactor.py:479: assert valid.model_dump() == {"type": "click"}
`

## dot_dict (2 hits)
`
backend\scratch_patch_slots_dict.py:40: c = c.replace('slot.get("dict")()', 'slot.model_dump() if hasattr(slot, "model_dump") else slot.dict() if hasattr(slot, "dict") else slot')
backend\scratch_patch_users_model_dump.py:5: c = c.replace('user_data.dict(exclude_unset=True)', 'user_data.model_dump(exclude_unset=True, by_alias=True)')
`

