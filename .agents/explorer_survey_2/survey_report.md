# Router `.get(` Scanner Survey Report

**Explorer**: Explorer 2 (Router Get Scanner Explorer)
**Date**: 2026-09-13
**Scope**: All router files in `backend/app/routers/`
**Reference Standard**: Pattern established in `backend/app/routers/ads.py`

---

## 1. Executive Summary

A complete static and AST analysis was executed across all router files in `backend/app/routers/` to identify, analyze, and categorize every instance of `.get(`.

- **Total Active Python Router Files**: 55 (including `__init__.py`)
- **Additional Tracked Router Files**: 2 (`analytics.py.tmp`, `orders.py.bak`)
- **Total Router Files Tracked in Repository**: 57 (57 total files)
- **Total `.get(` Instances in Active Routers**: 665
- **Category A (Dict Workarounds to Refactor)**: **387 calls** across **26 files**
- **Category B (Exempt Usages)**: **278 calls** across 55 files
  - *FastAPI `@router.get` route decorators*: 247 calls
  - *Exempt Standard Dict / Headers / Cache / DB Repository lookups*: 31 calls
- **Files Completely Clean of Category A**: **29 active router files**

---

## 2. Complete Inventory Table (All 55 Active Routers + 2 Legacy Files)

| # | Router File | Cat A (Dict Workarounds) | Cat B (Exempt) | Route Decorators (`@router.get`) | Total `.get(` Calls | Status |
|---|-------------|:------------------------:|:--------------:|:--------------------------------:|:-------------------:|:------:|
| 1 | `__init__.py` | **0** | 0 | 0 | 0 | ✅ Clean |
| 2 | `activity.py` | **0** | 2 | 0 | 2 | ✅ Clean |
| 3 | `ads.py` | **0** | 0 | 2 | 2 | ✅ Clean |
| 4 | `analytics.py` | **24** | 0 | 48 | 72 | ⚠️ Needs Refactor |
| 5 | `auth.py` | **17** | 0 | 1 | 18 | ⚠️ Needs Refactor |
| 6 | `availability_requests.py` | **7** | 0 | 2 | 9 | ⚠️ Needs Refactor |
| 7 | `banners.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 8 | `brands.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 9 | `bundles.py` | **0** | 1 | 6 | 7 | ✅ Clean |
| 10 | `cart.py` | **0** | 1 | 3 | 4 | ✅ Clean |
| 11 | `categories.py` | **0** | 0 | 7 | 7 | ✅ Clean |
| 12 | `category_tags.py` | **1** | 0 | 3 | 4 | ⚠️ Needs Refactor |
| 13 | `coach_marks.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 14 | `collections.py` | **0** | 0 | 5 | 5 | ✅ Clean |
| 15 | `commission.py` | **9** | 0 | 3 | 12 | ⚠️ Needs Refactor |
| 16 | `contacts.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 17 | `content_pages.py` | **2** | 5 | 7 | 14 | ⚠️ Needs Refactor |
| 18 | `coupons.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 19 | `customer_segments.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 20 | `delivery_charges.py` | **7** | 0 | 7 | 14 | ⚠️ Needs Refactor |
| 21 | `delivery_slots.py` | **55** | 0 | 4 | 59 | ⚠️ Needs Refactor |
| 22 | `delivery_zones.py` | **2** | 0 | 4 | 6 | ⚠️ Needs Refactor |
| 23 | `feature_flags.py` | **1** | 0 | 5 | 6 | ⚠️ Needs Refactor |
| 24 | `google_reviews.py` | **0** | 0 | 1 | 1 | ✅ Clean |
| 25 | `health.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 26 | `media.py` | **0** | 0 | 1 | 1 | ✅ Clean |
| 27 | `notifications.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 28 | `order_feedback.py` | **4** | 0 | 4 | 8 | ⚠️ Needs Refactor |
| 29 | `orders.py` | **134** | 8 | 8 | 150 | ⚠️ Needs Refactor |
| 30 | `page_info.py` | **5** | 0 | 3 | 8 | ⚠️ Needs Refactor |
| 31 | `payments.py` | **6** | 1 | 4 | 11 | ⚠️ Needs Refactor |
| 32 | `pincode_searches.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 33 | `pincodes.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 34 | `products.py` | **36** | 0 | 8 | 44 | ⚠️ Needs Refactor |
| 35 | `promo_strips.py` | **0** | 0 | 3 | 3 | ✅ Clean |
| 36 | `push_notifications.py` | **8** | 0 | 6 | 14 | ⚠️ Needs Refactor |
| 37 | `recommendations.py` | **13** | 6 | 4 | 23 | ⚠️ Needs Refactor |
| 38 | `referrals.py` | **2** | 0 | 3 | 5 | ⚠️ Needs Refactor |
| 39 | `return_settings.py` | **0** | 0 | 2 | 2 | ✅ Clean |
| 40 | `returns.py` | **15** | 2 | 5 | 22 | ⚠️ Needs Refactor |
| 41 | `reviews.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 42 | `schemes.py` | **0** | 0 | 4 | 4 | ✅ Clean |
| 43 | `search_tags.py` | **0** | 0 | 2 | 2 | ✅ Clean |
| 44 | `seller_availability.py` | **2** | 1 | 3 | 6 | ⚠️ Needs Refactor |
| 45 | `seller_payouts.py` | **0** | 0 | 5 | 5 | ✅ Clean |
| 46 | `seller_requests.py` | **1** | 0 | 3 | 4 | ⚠️ Needs Refactor |
| 47 | `support_tickets.py` | **4** | 0 | 3 | 7 | ⚠️ Needs Refactor |
| 48 | `system_settings.py` | **0** | 0 | 2 | 2 | ✅ Clean |
| 49 | `tracking.py` | **4** | 0 | 9 | 13 | ⚠️ Needs Refactor |
| 50 | `upi.py` | **0** | 0 | 1 | 1 | ✅ Clean |
| 51 | `users.py` | **21** | 1 | 8 | 30 | ⚠️ Needs Refactor |
| 52 | `valet_availability.py` | **4** | 1 | 3 | 8 | ⚠️ Needs Refactor |
| 53 | `valet_payout.py` | **3** | 0 | 3 | 6 | ⚠️ Needs Refactor |
| 54 | `version.py` | **0** | 1 | 2 | 3 | ✅ Clean |
| 55 | `wishlist.py` | **0** | 1 | 2 | 3 | ✅ Clean |
| 56 | `analytics.py.tmp` (legacy temp file) | 1 | 0 | 0 | 1 | ⚠️ Legacy Temp |
| 57 | `orders.py.bak` (pre-refactor backup) | 479 | 0 | 0 | 479 | ⚠️ Legacy Backup |
| | **Active Routers Total (55 files)** | **387** | **31** | **247** | **665** | |

---

## 3. Detailed Category A Inventory (Files Requiring Refactoring)

Each entry lists the file, line number, enclosing function/endpoint, code snippet, and the specific refactoring action required.

### `analytics.py` (24 Category A calls)

#### Function / Endpoint: `record_event` (23 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L187 | `event` | `'type'` | `if not event.get("type"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L202 | `enriched_event` | `'type'` | `event_type = enriched_event.get("type")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L203 | `enriched_event` | `'sessionId'` | `session_id = enriched_event.get("sessionId")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L204 | `enriched_event` | `'userId'` | `user_id = enriched_event.get("userId")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L194 | `user_info` | `'_id'` | `"userId": user_info.get("_id") if user_info else None,` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L195 | `event` | `'timestamp'` | `"timestamp": event.get("timestamp") or datetime.now(timezone.utc).isofor...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L205 | `enriched_event` | `'payload'` | `payload = enriched_event.get("payload") or {}` | Convert internal dict workaround to typed Pydantic dot-notation |
| L256 | `stored` | `'_id'` | `return {"status": "ok", "eventId": stored.get("_id")}` | Convert internal dict workaround to typed Pydantic dot-notation |
| L209 | `payload` | `'returning', False` | `is_returning = payload.get("returning", False)` | Define strict Pydantic request model and access via dot-notation |
| L212 | `enriched_event` | `'page', '/'` | `page = enriched_event.get("page", "/")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L215 | `payload` | `'productId'` | `product_id = payload.get("productId")` | Define strict Pydantic request model and access via dot-notation |
| L216 | `payload` | `'productName', 'Unknown'` | `product_name = payload.get("productName", "Unknown")` | Define strict Pydantic request model and access via dot-notation |
| L220 | `payload` | `'productId'` | `product_id = payload.get("productId")` | Define strict Pydantic request model and access via dot-notation |
| L221 | `payload` | `'productName', 'Unknown'` | `product_name = payload.get("productName", "Unknown")` | Define strict Pydantic request model and access via dot-notation |
| L222 | `payload` | `'source', 'mobile_app'` | `source = payload.get("source", "mobile_app")` | Define strict Pydantic request model and access via dot-notation |
| L226 | `payload` | `'productId'` | `product_id = payload.get("productId")` | Define strict Pydantic request model and access via dot-notation |
| L227 | `payload` | `'quantity', 1` | `quantity = payload.get("quantity", 1)` | Define strict Pydantic request model and access via dot-notation |
| L231 | `payload` | `'productId'` | `product_id = payload.get("productId")` | Define strict Pydantic request model and access via dot-notation |
| L232 | `payload` | `'quantity', 1` | `quantity = payload.get("quantity", 1)` | Define strict Pydantic request model and access via dot-notation |
| L236 | `payload` | `'query', ''` | `query = payload.get("query", "")` | Define strict Pydantic request model and access via dot-notation |
| L237 | `payload` | `'resultsCount', 0` | `results_count = payload.get("resultsCount", 0)` | Define strict Pydantic request model and access via dot-notation |
| L240 | `payload` | `'productId'` | `product_id = payload.get("productId")` | Define strict Pydantic request model and access via dot-notation |
| L244 | `payload` | `'reason', 'unknown'` | `reason = payload.get("reason", "unknown")` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `get_user_engagement_by_id` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L561 | `result` | `'error'` | `if result.get("error"):` | Convert internal dict workaround to typed Pydantic dot-notation |

### `auth.py` (17 Category A calls)

#### Function / Endpoint: `refresh_tokens` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L404 | `data` | `'userId'` | `user_id = data.get("userId")` | Define strict Pydantic request model and access via dot-notation |
| L405 | `data` | `'sessionId'` | `session_id = data.get("sessionId")` | Define strict Pydantic request model and access via dot-notation |
| L406 | `data` | `'refreshId'` | `refresh_id = data.get("refreshId")` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `send_otp` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L137 | `payload` | `'otp'` | `otp = payload.get("otp")` | Define strict Pydantic request model and access via dot-notation |
| L153 | `payload` | `'sent', True` | `response_data.sent = bool(payload.get("sent", True))` | Define strict Pydantic request model and access via dot-notation |
| L152 | `payload` | `'resend_available_in_seconds'` | `response_data.resendAvailableInSeconds = int(payload.get("resend_availab...` | Define strict Pydantic request model and access via dot-notation |
| L134 | `payload` | `'message', 'Too many requests'` | `detail=payload.get("message", "Too many requests"),` | Define strict Pydantic request model and access via dot-notation |
| L135 | `payload` | `'retry_after_seconds'` | `headers={"Retry-After": str(int(payload.get("retry_after_seconds") or 0))},` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `msg91_webhook` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L200 | `payload` | `'Status'` | `status_val = payload.get("Status") or payload.get("status") or payload.g...` | Define strict Pydantic request model and access via dot-notation |
| L200 | `payload` | `'status'` | `status_val = payload.get("Status") or payload.get("status") or payload.g...` | Define strict Pydantic request model and access via dot-notation |
| L200 | `payload` | `'type'` | `status_val = payload.get("Status") or payload.get("status") or payload.g...` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `register` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L290 | `otp_result` | `'valid'` | `if not otp_result.get("valid"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L289 | `otp_result` | `'valid'` | `logger.info(f"[REGISTER] OTP verify result: valid={otp_result.get('valid...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L293 | `otp_result` | `'message', 'Invalid or expired OTP'` | `detail=otp_result.get("message", "Invalid or expired OTP"),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `forgot_password` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L505 | `otp_result` | `'valid'` | `if not otp_result.get("valid"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L507 | `otp_result` | `'message', 'Invalid or expired OTP'` | `status_code=status.HTTP_400_BAD_REQUEST, detail=otp_result.get("message"...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `verify_msg91_token_endpoint` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L218 | `res_data` | `'message', 'Token verification failed'` | `status_code=status.HTTP_400_BAD_REQUEST, detail=res_data.get("message", ...` | Define strict Pydantic request model and access via dot-notation |

### `availability_requests.py` (7 Category A calls)

#### Function / Endpoint: `fulfill_availability_request` (7 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L129 | `result` | `'deliveredCount', 0` | `push_delivered = result.get("deliveredCount", 0)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L151 | `event` | `'userId'` | `ev_user_id = event.get("userId")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L152 | `event` | `'email'` | `ev_email = event.get("email")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L145 | `e` | `'type'` | `if e.get("type") == "notify_pincode"` | Convert internal dict workaround to typed Pydantic dot-notation |
| L148 | `e` | `'notified'` | `and not e.get("notified")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L146 | `e` | `'productId'` | `and str(e.get("productId")) == str(product_id)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L147 | `e` | `'pincode'` | `and str(e.get("pincode")) == str(pincode)` | Convert internal dict workaround to typed Pydantic dot-notation |

### `category_tags.py` (1 Category A calls)

#### Function / Endpoint: `update_category_tag` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L101 | `existing_tag` | `'_id'` | `if existing_tag and existing_tag.get("_id") != tag_id:` | Convert internal dict workaround to typed Pydantic dot-notation |

### `commission.py` (9 Category A calls)

#### Function / Endpoint: `resolve_commission_pct` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L135 | `tier` | `'minOrderValue', 0` | `min_v = tier.get("minOrderValue", 0)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L136 | `tier` | `'maxOrderValue'` | `max_v = tier.get("maxOrderValue")  # None = unlimited` | Convert internal dict workaround to typed Pydantic dot-notation |
| L138 | `tier` | `'commissionPct', default_pct` | `return float(tier.get("commissionPct", default_pct))` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `update_commission_tiers` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L260 | `sorted_tiers[i]` | `'maxOrderValue'` | `curr_max = sorted_tiers[i].get("maxOrderValue")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L279 | `updated` | `'tiers', []` | `"tiers": updated.get("tiers", []),` | Access updated entity model attributes with dot-notation |
| L280 | `updated` | `'defaultCommissionPct', 5.0` | `"defaultCommissionPct": updated.get("defaultCommissionPct", 5.0),` | Access updated entity model attributes with dot-notation |
| L253 | `d` | `'id'` | `if not d.get("id"):` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `set_seller_commission_override` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L340 | `updated` | `'commissionOverridePct'` | `"commissionOverridePct": updated.get("commissionOverridePct"),` | Access updated entity model attributes with dot-notation |

#### Function / Endpoint: `realize_pending_commissions` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L403 | `updated` | `'commissionStatus'` | `if updated.get("commissionStatus") == "realized":` | Access updated entity model attributes with dot-notation |

### `content_pages.py` (2 Category A calls)

#### Function / Endpoint: `update_privacy` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L178 | `result` | `'version', 1` | `version = result.get("version", 1)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L177 | `result` | `'lastUpdated', ''` | `last_updated = data.lastUpdated or result.get("lastUpdated", "")` | Convert internal dict workaround to typed Pydantic dot-notation |

### `delivery_charges.py` (7 Category A calls)

#### Function / Endpoint: `get_delivery_charge_by_location` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L90 | `result` | `'charge', 0.0` | `charge = result.get("charge", 0.0) or 0.0` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `update_delivery_charge` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L357 | `update_dict` | `'serviceableForCustomer'` | `if update_dict.get("serviceableForCustomer") is False:` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `check_serviceability` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L234 | `slot_config` | `'slots', []` | `for slot in slot_config.get("slots", []):` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L168 | `seller_doc` | `'name', ''` | `"companyName": (seller_doc.company_name if seller_doc.company_name is no...` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L169 | `seller_doc.address or {}` | `'city'` | `"city": seller_doc.city or (seller_doc.address or {}).get("city"),` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L188 | `seller_doc` | `'name', ''` | `"companyName": (seller_doc.company_name if seller_doc.company_name is no...` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L189 | `seller_doc.address or {}` | `'city'` | `"city": seller_doc.city or (seller_doc.address or {}).get("city"),` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |

### `delivery_slots.py` (55 Category A calls)

#### Function / Endpoint: `get_available_slots` (23 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L141 | `config` | `'slots', []` | `for slot in config.get("slots", []):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L179 | `slot` | `'endTime', ''` | `end_time_str = slot.get("endTime", "")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L146 | `slot` | `'isFullDay'` | `is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not Non...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L147 | `slot` | `'isUrgent'` | `is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L143 | `slot` | `'isActive'` | `if not (slot.get("isActive") if slot.get("isActive") is not None else Tr...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L146 | `slot` | `'isFullDay'` | `is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not Non...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L147 | `slot` | `'isUrgent'` | `is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L157 | `slot` | `'cutoffHours'` | `cutoff_hours = slot.get("cutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L173 | `config` | `'zoneDefaultCapacity'` | `cap = config.get("zoneDefaultCapacity")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L192 | `slot` | `'id', f"{slot.get('startTime')}-{slot.get('endTime')}"` | `"slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L193 | `slot` | `'startTime', ''` | `"startTime": slot.get("startTime", ""),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L194 | `slot` | `'endTime', ''` | `"endTime": slot.get("endTime", ""),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L143 | `slot` | `'isActive'` | `if not (slot.get("isActive") if slot.get("isActive") is not None else Tr...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L152 | `slot` | `'urgentCutoffHours'` | `slot.get("urgentCutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L154 | `slot` | `'cutoffHours'` | `else slot.get("cutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L171 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L171 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L174 | `slot` | `'bookedCount'` | `booked = int(slot.get("bookedCount") or 0)` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L153 | `slot` | `'urgentCutoffHours'` | `if slot.get("urgentCutoffHours") is not None` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L160 | `slot` | `'endTime'` | `anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.ge...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L160 | `slot` | `'startTime'` | `anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.ge...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L192 | `slot` | `'startTime'` | `"slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L192 | `slot` | `'endTime'` | `"slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |

#### Function / Endpoint: `book_slot` (9 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L291 | `config` | `'slots', []` | `slots = config.get("slots", [])` | Convert internal dict workaround to typed Pydantic dot-notation |
| L294 | `slot` | `'id'` | `if slot.get("id") == slot_id or f"{slot.get('startTime')}-{slot.get('end...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L297 | `config` | `'zoneDefaultCapacity'` | `cap = config.get("zoneDefaultCapacity")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L295 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L295 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L298 | `slot` | `'bookedCount'` | `booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L298 | `slot` | `'bookedCount'` | `booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L294 | `slot` | `'startTime'` | `if slot.get("id") == slot_id or f"{slot.get('startTime')}-{slot.get('end...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L294 | `slot` | `'endTime'` | `if slot.get("id") == slot_id or f"{slot.get('startTime')}-{slot.get('end...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |

#### Function / Endpoint: `get_dates_with_slots` (18 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L230 | `config` | `'slots', []` | `for slot in config.get("slots", []):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L234 | `slot` | `'isFullDay'` | `is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not Non...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L235 | `slot` | `'isUrgent'` | `is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L250 | `slot` | `'endTime'` | `end_time_str = (slot.get("endTime") or "")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L231 | `slot` | `'isActive'` | `if not (slot.get("isActive") if slot.get("isActive") is not None else Tr...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L234 | `slot` | `'isFullDay'` | `is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not Non...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L235 | `slot` | `'isUrgent'` | `is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L239 | `slot` | `'urgentCutoffHours'` | `cutoff_hours = slot.get("urgentCutoffHours") if is_urgent and slot.get("...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L239 | `slot` | `'cutoffHours'` | `cutoff_hours = slot.get("urgentCutoffHours") if is_urgent and slot.get("...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L262 | `config` | `'zoneDefaultCapacity'` | `cap = config.get("zoneDefaultCapacity")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L231 | `slot` | `'isActive'` | `if not (slot.get("isActive") if slot.get("isActive") is not None else Tr...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L260 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L260 | `slot` | `'capacity'` | `cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, ""...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L263 | `slot` | `'bookedCount'` | `booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L263 | `slot` | `'bookedCount'` | `booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L239 | `slot` | `'urgentCutoffHours'` | `cutoff_hours = slot.get("urgentCutoffHours") if is_urgent and slot.get("...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L241 | `slot` | `'endTime'` | `anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.ge...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L241 | `slot` | `'startTime'` | `anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.ge...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |

#### Function / Endpoint: `_resolve_zone_config` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L82 | `zone_data` | `'_id'` | `zone_id = zone_data.get("_id") or zone_data.get("id") if zone_data else ...` | Define strict Pydantic request model and access via dot-notation |
| L82 | `zone_data` | `'id'` | `zone_id = zone_data.get("_id") or zone_data.get("id") if zone_data else ...` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `create_delivery_slot_config` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L332 | `zone_doc` | `'defaultCapacity', 10` | `zone_default_capacity = zone_doc.get("defaultCapacity", 10)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L338 | `slot_dict` | `'capacity'` | `if slot_dict.get("capacity") is None or slot_dict.get("capacity") == 0:` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L338 | `slot_dict` | `'capacity'` | `if slot_dict.get("capacity") is None or slot_dict.get("capacity") == 0:` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |

### `delivery_zones.py` (2 Category A calls)

#### Function / Endpoint: `_check_pincode_conflicts` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L74 | `z` | `'pincodes'` | `for pc in z.get("pincodes") or []:` | Convert internal dict workaround to typed Pydantic dot-notation |
| L75 | `z` | `'name', str(z['_id'])` | `taken[pc] = z.get("name", str(z["_id"]))` | Convert internal dict workaround to typed Pydantic dot-notation |

### `feature_flags.py` (1 Category A calls)

#### Function / Endpoint: `toggle_feature_flag` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L141 | `flag` | `'enabled', False` | `updated = await feature_flag_repository.update(flag["_id"], {"enabled": ...` | Convert internal dict workaround to typed Pydantic dot-notation |

### `order_feedback.py` (4 Category A calls)

#### Function / Endpoint: `get_eligible_feedback_order` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L106 | `latest_eligible_order` | `'_id'` | `return {"eligibleOrderId": latest_eligible_order.get("_id")}` | Convert internal dict workaround to typed Pydantic dot-notation |
| L70 | `f` | `'orderId'` | `feedback_order_ids = set(f.get("orderId") for f in feedbacks)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L80 | `latest_eligible_order` | `'_id'` | `return {"eligibleOrderId": latest_eligible_order.get("_id")}` | Convert internal dict workaround to typed Pydantic dot-notation |
| L92 | `latest_feedback` | `'createdAt'` | `latest_feedback_date = parser.parse(latest_feedback.get("createdAt"))` | Convert internal dict workaround to typed Pydantic dot-notation |

### `orders.py` (134 Category A calls)

#### Function / Endpoint: `create_order` (103 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L574 | `validation` | `'eligibleItemIndices'` | `eligible_item_indices = validation.get("eligibleItemIndices")` | Replace with `CouponValidationResult` model dot-notation |
| L575 | `validation` | `'itemDiscounts'` | `item_discounts = validation.get("itemDiscounts")` | Replace with `CouponValidationResult` model dot-notation |
| L576 | `validation` | `'bxgyItemIndices'` | `validation.get("bxgyItemIndices")` | Replace with `CouponValidationResult` model dot-notation |
| L717 | `ref_settings` | `'retail', {}` | `retail_settings = ref_settings.get("retail", {})` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1012 | `order_data.shippingAddress` | `'zipCode'` | `if order_data.shippingAddress and order_data.shippingAddress.get("zipCod...` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L522 | `order_data.shippingAddress` | `'state', ''` | `state = order_data.shippingAddress.get("state", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L523 | `order_data.shippingAddress` | `'city', ''` | `city = order_data.shippingAddress.get("city", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L524 | `order_data.shippingAddress` | `'district', ''` | `district = order_data.shippingAddress.get("district", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L525 | `order_data.shippingAddress` | `'zipCode', ''` | `zip_code = order_data.shippingAddress.get("zipCode", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L569 | `validation` | `'valid'` | `if not validation.get("valid"):` | Replace with `CouponValidationResult` model dot-notation |
| L572 | `validation['coupon']` | `'code'` | `coupon_code = validation["coupon"].get("code") or ("AUTO-" + (applied_co...` | Replace with `CouponValidationResult` model dot-notation |
| L578 | `validation` | `'coupon'` | `c_obj = validation.get("coupon") or {}` | Replace with `CouponValidationResult` model dot-notation |
| L587 | `validation['coupon']` | `'typeOfDiscount'` | `"typeOfDiscount": validation["coupon"].get("typeOfDiscount"),` | Replace with `CouponValidationResult` model dot-notation |
| L605 | `best` | `'eligibleItemIndices'` | `eligible_item_indices = best.get("eligibleItemIndices")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L606 | `best` | `'itemDiscounts'` | `item_discounts = best.get("itemDiscounts")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L607 | `best` | `'bxgyItemIndices'` | `best.get("bxgyItemIndices")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L657 | `coupon_info` | `'typeOfDiscount'` | `is_shipping_discount = coupon_info is not None and coupon_info.get("type...` | Replace with `CouponValidationResult` model dot-notation |
| L752 | `order_data.shippingAddress` | `'zipCode'` | `(order_data.shippingAddress.get("zipCode") or order_data.shippingAddress...` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L752 | `order_data.shippingAddress` | `'pincode'` | `(order_data.shippingAddress.get("zipCode") or order_data.shippingAddress...` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L869 | `order_data.shippingAddress` | `'zipCode', ''` | `zip_code = order_data.shippingAddress.get("zipCode", "") if order_data.s...` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L910 | `sc` | `'slots', []` | `for sl in sc.get("slots", []):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1000 | `matched_slot` | `'_id', matched_slot.get('id')` | `"slotId": matched_slot.get("_id", matched_slot.get("id")),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1063 | `order_data.shippingAddress` | `'state', ''` | `state = order_data.shippingAddress.get("state", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1064 | `order_data.shippingAddress` | `'city', ''` | `city = order_data.shippingAddress.get("city", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1065 | `order_data.shippingAddress` | `'district', ''` | `district = order_data.shippingAddress.get("district", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1066 | `order_data.shippingAddress` | `'zipCode', ''` | `zip_code = order_data.shippingAddress.get("zipCode", "")` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1118 | `coupon_info` | `'typeOfDiscount'` | `is_shipping_discount = coupon_info is not None and coupon_info.get("type...` | Replace with `CouponValidationResult` model dot-notation |
| L1443 | `populated_order` | `'user', {}` | `email = populated_order.get("user", {}).email if populated_order.user el...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1475 | `oi` | `'sellerId'` | `sid = oi.get("sellerId")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L533 | `delivery_charge_data` | `'charge', 0` | `charge_amount = delivery_charge_data.get("charge", 0)` | Define strict Pydantic request model and access via dot-notation |
| L534 | `delivery_charge_data` | `'minCartValue', 0` | `min_cart_value_for_free = delivery_charge_data.get("minCartValue", 0)` | Define strict Pydantic request model and access via dot-notation |
| L535 | `delivery_charge_data` | `'isApplicableToRole', True` | `if delivery_charge_data.get("isApplicableToRole", True):` | Define strict Pydantic request model and access via dot-notation |
| L579 | `c_obj` | `'method'` | `if c_obj.get("method") == "discount_code" and c_obj.get("couponMode") ==...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L579 | `c_obj` | `'couponMode'` | `if c_obj.get("method") == "discount_code" and c_obj.get("couponMode") ==...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L917 | `sl` | `'capacity'` | `_cap = sl.get("capacity")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L967 | `matched_slot` | `'isFullDay'` | `is_full_day = (matched_slot.get("isFullDay") if matched_slot.get("isFull...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L970 | `matched_slot` | `'capacity'` | `_cap = matched_slot.get("capacity")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L999 | `matched_config` | `'_id', matched_config.get('id')` | `"configId": str(matched_config.get("_id", matched_config.get("id"))),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1000 | `matched_slot` | `'id'` | `"slotId": matched_slot.get("_id", matched_slot.get("id")),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1005 | `matched_slot` | `'isUrgent'` | `"isUrgent": (matched_slot.get("isUrgent") if matched_slot.get("isUrgent"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1077 | `delivery_charge_data` | `'charge', 0` | `charge_amount = delivery_charge_data.get("charge", 0)` | Define strict Pydantic request model and access via dot-notation |
| L1078 | `delivery_charge_data` | `'minCartValue', 0` | `min_cart_value_for_free = delivery_charge_data.get("minCartValue", 0)` | Define strict Pydantic request model and access via dot-notation |
| L1083 | `delivery_charge_data` | `'isApplicableToRole', True` | `if delivery_charge_data.get("isApplicableToRole", True):` | Define strict Pydantic request model and access via dot-notation |
| L570 | `validation` | `'message'` | `raise HTTPException(status_code=400, detail=validation.get("message"))` | Replace with `CouponValidationResult` model dot-notation |
| L884 | `_zone_doc` | `'_id', _zone_doc.get('id')` | `order_zone_id = str(_zone_doc.get("_id", _zone_doc.get("id")))` | Convert internal dict workaround to typed Pydantic dot-notation |
| L885 | `_zone_doc` | `'urgentDeliveryAvailable', False` | `zone_urgent_available = bool(_zone_doc.get("urgentDeliveryAvailable", Fa...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L919 | `sc` | `'zoneDefaultCapacity'` | `_cap = sc.get("zoneDefaultCapacity")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L920 | `sl` | `'bookedCount'` | `_booked = (sl.get("bookedCount") if sl.get("bookedCount") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L967 | `matched_slot` | `'isFullDay'` | `is_full_day = (matched_slot.get("isFullDay") if matched_slot.get("isFull...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L972 | `matched_config` | `'zoneDefaultCapacity'` | `_cap = matched_config.get("zoneDefaultCapacity")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L973 | `matched_slot` | `'bookedCount'` | `_booked = (matched_slot.get("bookedCount") if matched_slot.get("bookedCo...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L978 | `matched_slot` | `'urgentCutoffHours'` | `matched_slot.get("urgentCutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L980 | `matched_slot` | `'cutoffHours'` | `else matched_slot.get("cutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L999 | `matched_config` | `'id'` | `"configId": str(matched_config.get("_id", matched_config.get("id"))),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1005 | `matched_slot` | `'isUrgent'` | `"isUrgent": (matched_slot.get("isUrgent") if matched_slot.get("isUrgent"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1013 | `order_data.shippingAddress` | `'zipCode'` | `shipping_zip = str(order_data.shippingAddress.get("zipCode")).strip()` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1035 | `sdoc.get('sellerPermissions') or {}` | `'serviceableZoneIds', []` | `seller_zone_ids = (sdoc.get("sellerPermissions") or {}).get("serviceable...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1261 | `selected_slot_info` | `'configId'` | `selected_slot_info.get("configId"),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1262 | `selected_slot_info` | `'slotId'` | `selected_slot_info.get("slotId"),` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1459 | `oi` | `'sellerId'` | `if not oi.get("sellerId") and super_admin_id:` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1522 | `sdo` | `'deliverySlotId'` | `if sdo and sdo.get("deliverySlotId") and sdo.get("deliverySlotDate"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1522 | `sdo` | `'deliverySlotDate'` | `if sdo and sdo.get("deliverySlotId") and sdo.get("deliverySlotDate"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L432 | `entry` | `'amount', 0.0` | `entry.get("amount", 0.0) for entry in (p.payment_entries or []) if entry...` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |
| L884 | `_zone_doc` | `'id'` | `order_zone_id = str(_zone_doc.get("_id", _zone_doc.get("id")))` | Convert internal dict workaround to typed Pydantic dot-notation |
| L911 | `sl` | `'isActive'` | `if not (sl.get("isActive") if sl.get("isActive") is not None else True):` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L920 | `sl` | `'bookedCount'` | `_booked = (sl.get("bookedCount") if sl.get("bookedCount") is not None el...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L926 | `sl` | `'isUrgent'` | `if (sl.get("isUrgent") if sl.get("isUrgent") is not None else False):` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L973 | `matched_slot` | `'bookedCount'` | `_booked = (matched_slot.get("bookedCount") if matched_slot.get("bookedCo...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L979 | `matched_slot` | `'isUrgent'` | `if matched_slot.get("isUrgent") and matched_slot.get("urgentCutoffHours"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L985 | `matched_slot` | `'isUrgent'` | `is_urgent = (matched_slot.get("isUrgent") if matched_slot.get("isUrgent"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1233 | `slot_config` | `'_db_id'` | `db_id = slot_config.get("_db_id") or config_id` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1284 | `spec` | `'productId', ''` | `spec_pid = str(spec.get("productId", ""))` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1487 | `sdo` | `'sellerId'` | `seller_delivery_map[sdo.get("sellerId")] = sdo` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1492 | `order_data.shippingAddress` | `'state', ''` | `order_data.shippingAddress.get("state", ""),` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1493 | `order_data.shippingAddress` | `'city', ''` | `order_data.shippingAddress.get("city", ""),` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1494 | `order_data.shippingAddress` | `'district', ''` | `order_data.shippingAddress.get("district", ""),` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1495 | `order_data.shippingAddress` | `'zipCode', ''` | `order_data.shippingAddress.get("zipCode", ""),` | Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model |
| L1524 | `sdo` | `'deliverySlotConfigId'` | `"configId": sdo.get("deliverySlotConfigId"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1525 | `sdo` | `'deliverySlotId'` | `"slotId": sdo.get("deliverySlotId"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1526 | `sdo` | `'deliverySlotDate'` | `"date": sdo.get("deliverySlotDate"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L432 | `entry` | `'verified'` | `entry.get("amount", 0.0) for entry in (p.payment_entries or []) if entry...` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |
| L911 | `sl` | `'isActive'` | `if not (sl.get("isActive") if sl.get("isActive") is not None else True):` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L926 | `sl` | `'isUrgent'` | `if (sl.get("isUrgent") if sl.get("isUrgent") is not None else False):` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L929 | `sl` | `'urgentCutoffHours'` | `sl.get("urgentCutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L931 | `sl` | `'cutoffHours'` | `else sl.get("cutoffHours")` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L950 | `sl` | `'id'` | `if (sl.get("id") or f"{sl.get('startTime')}-{sl.get('endTime')}") == ord...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L979 | `matched_slot` | `'urgentCutoffHours'` | `if matched_slot.get("isUrgent") and matched_slot.get("urgentCutoffHours"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L985 | `matched_slot` | `'isUrgent'` | `is_urgent = (matched_slot.get("isUrgent") if matched_slot.get("isUrgent"...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L987 | `matched_slot` | `'endTime'` | `(matched_slot.get("endTime") or "") if is_urgent else (matched_slot.get(...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L987 | `matched_slot` | `'startTime'` | `(matched_slot.get("endTime") or "") if is_urgent else (matched_slot.get(...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1038 | `sdoc` | `'companyName'` | `s_name = sdoc.get("companyName") or sdoc.get("name") or "Seller"` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1038 | `sdoc` | `'name'` | `s_name = sdoc.get("companyName") or sdoc.get("name") or "Seller"` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1089 | `delivery_charge_data` | `'urgentDeliveryCharge'` | `urgent_charge = delivery_charge_data.get("urgentDeliveryCharge")` | Define strict Pydantic request model and access via dot-notation |
| L1283 | `spec` | `'quantity', 1` | `spec_qty = max(1, spec.get("quantity", 1) or 1)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1293 | `ref_item` | `'quantity', spec_qty` | `copies = max(1, ref_item.get("quantity", spec_qty) // spec_qty)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1542 | `sdoc` | `'companyName'` | `seller_name = sdoc.get("companyName") or sdoc.get("name") or ""` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1542 | `sdoc` | `'name'` | `seller_name = sdoc.get("companyName") or sdoc.get("name") or ""` | Convert internal dict workaround to typed Pydantic dot-notation |
| L930 | `sl` | `'urgentCutoffHours'` | `if sl.get("urgentCutoffHours") is not None` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1035 | `sdoc` | `'sellerPermissions'` | `seller_zone_ids = (sdoc.get("sellerPermissions") or {}).get("serviceable...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L950 | `sl` | `'startTime'` | `if (sl.get("id") or f"{sl.get('startTime')}-{sl.get('endTime')}") == ord...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L950 | `sl` | `'endTime'` | `if (sl.get("id") or f"{sl.get('startTime')}-{sl.get('endTime')}") == ord...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1247 | `sl` | `'bookedCount'` | `sl["bookedCount"] = (sl.get("bookedCount") if sl.get("bookedCount") is n...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1247 | `sl` | `'bookedCount'` | `sl["bookedCount"] = (sl.get("bookedCount") if sl.get("bookedCount") is n...` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |

#### Function / Endpoint: `settle_credit` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L2728 | `updated_payment` | `'amountRemaining', 0` | `if updated_payment.get("amountRemaining", 0) <= 0:` | Access updated entity model attributes with dot-notation |
| L2708 | `payment` | `'totalAmount', 0` | `remaining_amount = (payment.amount_remaining if payment.amount_remaining...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `populate_orders` (11 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L236 | `item_dict` | `'product'` | `prod = item_dict.get("product")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L276 | `valet` | `'name'` | `v_name = valet.get("name") if isinstance(valet, dict) else (valet.name i...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L277 | `valet` | `'phone'` | `v_phone = valet.get("phone") if isinstance(valet, dict) else (valet.phon...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L275 | `valet` | `'_id'` | `v_id = valet.get("_id") or valet.get("id") if isinstance(valet, dict) el...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L275 | `valet` | `'id'` | `v_id = valet.get("_id") or valet.get("id") if isinstance(valet, dict) el...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L169 | `prod` | `'_id'` | `pid = prod.get("_id") or prod.get("id")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L169 | `prod` | `'id'` | `pid = prod.get("_id") or prod.get("id")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L190 | `prod` | `'_id'` | `pid = prod.get("_id") or prod.get("id")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L190 | `prod` | `'id'` | `pid = prod.get("_id") or prod.get("id")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L238 | `prod` | `'_id'` | `prod_id = str(prod.get("_id") or prod.get("id"))` | Convert internal dict workaround to typed Pydantic dot-notation |
| L238 | `prod` | `'id'` | `prod_id = str(prod.get("_id") or prod.get("id"))` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `update_order_status` (12 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L1947 | `updated_order` | `'subOrderIds'` | `sub_ids = updated_order.get("subOrderIds") or []` | Access updated entity model attributes with dot-notation |
| L1978 | `updated_order` | `'subOrderIds'` | `_f_status = await _compute_fulfillment_status(updated_order.get("subOrde...` | Access updated entity model attributes with dot-notation |
| L1984 | `populated_order` | `'user', {}` | `email = populated_order.get("user", {}).email if populated_order.user el...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1990 | `updated_order` | `'invoicePath'` | `if order_user and order_user.role == "customer" and not updated_order.ge...` | Access updated entity model attributes with dot-notation |
| L1827 | `slot_config` | `'slots', []` | `slots_list = slot_config.get("slots", [])` | Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`) |
| L1850 | `payment['paymentEntries'][0]` | `'entryId'` | `payment["paymentEntries"][0].get("entryId"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1906 | `new_payment` | `'orderId'` | `"orderId": new_payment.get("orderId"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1907 | `new_payment` | `'totalAmount', 0` | `"totalAmount": new_payment.get("totalAmount", 0),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1871 | `updated_payment_with_entry` | `'orderId'` | `"orderId": updated_payment_with_entry.get("orderId"),` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |
| L1905 | `new_payment` | `'paymentId'` | `"paymentId": new_payment.get("paymentId") or new_payment.id,` | Convert internal dict workaround to typed Pydantic dot-notation |
| L1869 | `updated_payment_with_entry` | `'paymentId'` | `"paymentId": updated_payment_with_entry.get("paymentId")` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |
| L1872 | `payment` | `'totalAmount', 0` | `"totalAmount": (order.total if order.total is not None else payment.get(...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `update_seller_order_status` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L2899 | `parent` | `'subOrderIds'` | `if parent and parent.get("subOrderIds"):` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `_resolve_product_seller_id` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L47 | `sellers[0]` | `'id'` | `return sellers[0].get("id") or sellers[0].get("_id")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L47 | `sellers[0]` | `'_id'` | `return sellers[0].get("id") or sellers[0].get("_id")` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `accept_order` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L2045 | `entry` | `'verified'` | `any_verified = any(entry.get("verified") for entry in entries)` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |

#### Function / Endpoint: `valet_response` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L2421 | `_so` | `'sellerId'` | `_seller_id = _so.get("sellerId")` | Convert internal dict workaround to typed Pydantic dot-notation |
| L2497 | `d` | `'valetId'` | `if valet_id and not any(isinstance(d, dict) and d.get("valetId") == vale...` | Convert internal dict workaround to typed Pydantic dot-notation |

### `page_info.py` (5 Category A calls)

#### Function / Endpoint: `get_page_info` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L34 | `page_info.get('pages', {})` | `page_id` | `page_data = page_info.get("pages", {}).get(page_id)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L41 | `page_data` | `'columns', {}` | `"columns": page_data.get("columns", {}),` | Define strict Pydantic request model and access via dot-notation |
| L34 | `page_info` | `'pages', {}` | `page_data = page_info.get("pages", {}).get(page_id)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L40 | `page_data` | `'title'` | `"page": {"title": page_data.get("title"), "description": page_data.get("...` | Define strict Pydantic request model and access via dot-notation |
| L40 | `page_data` | `'description'` | `"page": {"title": page_data.get("title"), "description": page_data.get("...` | Define strict Pydantic request model and access via dot-notation |

### `payments.py` (6 Category A calls)

#### Function / Endpoint: `get_wholesaler_dues` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L57 | `entry` | `'amount', 0.0` | `entry.get("amount", 0.0) for entry in (p.payment_entries or []) if entry...` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |
| L57 | `entry` | `'verified'` | `entry.get("amount", 0.0) for entry in (p.payment_entries or []) if entry...` | Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`) |

#### Function / Endpoint: `submit_credit_settlement` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L321 | `updated_payment` | `'paymentId'` | `payment_id = updated_payment.get("paymentId") or updated_payment.get("_id")` | Access updated entity model attributes with dot-notation |
| L321 | `updated_payment` | `'_id'` | `payment_id = updated_payment.get("paymentId") or updated_payment.get("_id")` | Access updated entity model attributes with dot-notation |
| L329 | `updated_payment` | `'_id'` | `"paymentId": updated_payment.get("_id"),` | Access updated entity model attributes with dot-notation |
| L331 | `updated_payment` | `'orderId'` | `"orderId": updated_payment.get("orderId"),` | Access updated entity model attributes with dot-notation |

### `products.py` (36 Category A calls)

#### Function / Endpoint: `get_product_search_tags` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L980 | `products_with_tags[0]` | `'searchTags', []` | `resolved = products_with_tags[0].get("searchTags", [])` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_public_products` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L656 | `facets` | `'brands', []` | `"brands": facets.get("brands", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L657 | `facets` | `'categories', []` | `"categories": facets.get("categories", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L658 | `facets` | `'subCategories', []` | `"subCategories": facets.get("subCategories", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L659 | `facets` | `'collections', []` | `"collections": facets.get("collections", []),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_products` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L807 | `facets` | `'brands', []` | `"brands": facets.get("brands", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L808 | `facets` | `'categories', []` | `"categories": facets.get("categories", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L809 | `facets` | `'subCategories', []` | `"subCategories": facets.get("subCategories", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L810 | `facets` | `'collections', []` | `"collections": facets.get("collections", []),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `populate_product_discounts` (9 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L494 | `default_coupon` | `'minRequirementType'` | `if default_coupon and default_coupon.get("minRequirementType") == "quant...` | Replace with `CouponValidationResult` model dot-notation |
| L503 | `qty_coupon` | `'quantityTiers'` | `p.quantityTiers = qty_coupon.get("quantityTiers") or []` | Replace with `CouponValidationResult` model dot-notation |
| L504 | `qty_coupon` | `'applicableItemType'` | `p.quantityItemType = qty_coupon.get("applicableItemType") or "units"` | Replace with `CouponValidationResult` model dot-notation |
| L507 | `default_coupon` | `'minRequirementType'` | `if default_coupon and default_coupon.get("minRequirementType") == "quant...` | Replace with `CouponValidationResult` model dot-notation |
| L498 | `oc` | `'minRequirementType'` | `if oc.get("minRequirementType") == "quantity_based":` | Convert internal dict workaround to typed Pydantic dot-notation |
| L510 | `default_coupon` | `'typeOfDiscount'` | `"type": default_coupon.get("typeOfDiscount"),` | Replace with `CouponValidationResult` model dot-notation |
| L511 | `default_coupon` | `'code'` | `"code": default_coupon.get("code"),` | Replace with `CouponValidationResult` model dot-notation |
| L519 | `oc` | `'typeOfDiscount'` | `"type": oc.get("typeOfDiscount"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L520 | `oc` | `'code'` | `"code": oc.get("code"),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `upload_csv` (17 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L118 | `main_row` | `'quantityPerCase'` | `if main_row.get("quantityPerCase") and str(main_row.get("quantityPerCase...` | Access Pydantic `CsvProductRow` model attributes directly |
| L138 | `main_row` | `'images'` | `"images": [img.strip() for img in main_row.get("images", "").split(",") ...` | Access Pydantic `CsvProductRow` model attributes directly |
| L139 | `main_row` | `'videos'` | `"videos": [vid.strip() for vid in main_row.get("videos", "").split(",") ...` | Access Pydantic `CsvProductRow` model attributes directly |
| L126 | `main_row` | `'productId', ''` | `"productIdFormatted": main_row.get("productId", "").strip(),` | Access Pydantic `CsvProductRow` model attributes directly |
| L127 | `main_row` | `'sku', ''` | `"sku": main_row.get("sku", "").strip(),` | Access Pydantic `CsvProductRow` model attributes directly |
| L129 | `main_row` | `'subCategory', ''` | `"subCategory": main_row.get("subCategory", "").strip(),` | Access Pydantic `CsvProductRow` model attributes directly |
| L130 | `main_row` | `'description', ''` | `"description": main_row.get("description", "").strip(),` | Access Pydantic `CsvProductRow` model attributes directly |
| L131 | `main_row` | `'brand', ''` | `"brand": main_row.get("brand", "").strip(),` | Access Pydantic `CsvProductRow` model attributes directly |
| L209 | `main_row` | `'_row_number', 'N/A'` | `{"row": main_row.get("_row_number", "N/A"), "product": name, "error": f"...` | Access Pydantic `CsvProductRow` model attributes directly |
| L214 | `main_row` | `'_row_number', 'N/A'` | `{"row": main_row.get("_row_number", "N/A"), "product": name, "error": f"...` | Access Pydantic `CsvProductRow` model attributes directly |
| L112 | `main_row` | `'mrpPerCase', ''` | `if main_row.mrp_per_case and str(main_row.get("mrpPerCase", "")).strip():` | Access Pydantic `CsvProductRow` model attributes directly |
| L118 | `main_row` | `'quantityPerCase', ''` | `if main_row.get("quantityPerCase") and str(main_row.get("quantityPerCase...` | Access Pydantic `CsvProductRow` model attributes directly |
| L132 | `main_row` | `'collection', ''` | `"collection": main_row.get("collection", "").strip() or None,` | Access Pydantic `CsvProductRow` model attributes directly |
| L137 | `main_row` | `'isActive', 'true'` | `"isActive": main_row.get("isActive", "true").lower() in ["true", "1", "y...` | Access Pydantic `CsvProductRow` model attributes directly |
| L168 | `row` | `val_key, ''` | `variant_val = row.get(val_key, "").strip()` | Access Pydantic `CsvProductRow` model attributes directly |
| L138 | `main_row` | `'images', ''` | `"images": [img.strip() for img in main_row.get("images", "").split(",") ...` | Access Pydantic `CsvProductRow` model attributes directly |
| L139 | `main_row` | `'videos', ''` | `"videos": [vid.strip() for vid in main_row.get("videos", "").split(",") ...` | Access Pydantic `CsvProductRow` model attributes directly |

#### Function / Endpoint: `export_csv` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L297 | `combo` | `'attributes', {}` | `combo_attrs = combo.get("attributes", {}) or {}` | Convert internal dict workaround to typed Pydantic dot-notation |

### `push_notifications.py` (8 Category A calls)

#### Function / Endpoint: `register_device` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L303 | `request.subscription` | `'endpoint'` | `has_web_subscription = request.subscription and request.subscription.get...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_notification_inbox` (7 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L219 | `n` | `'_id'` | `"_id": n.get("_id"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L220 | `n` | `'title', ''` | `"title": n.get("title", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L221 | `n` | `'message', ''` | `"message": n.get("message", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L222 | `n` | `'image'` | `"image": n.get("image"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L223 | `n` | `'link'` | `"link": n.get("link"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L224 | `n` | `'createdAt'` | `"createdAt": n.get("createdAt"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L229 | `n` | `'createdAt'` | `inbox.sort(key=lambda n: n.get("createdAt") or "", reverse=True)` | Convert internal dict workaround to typed Pydantic dot-notation |

### `recommendations.py` (13 Category A calls)

#### Function / Endpoint: `get_favourites_page` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L246 | `p_copy` | `'displayImage'` | `p_copy["displayImage"] = p_copy.get("displayImage") or (` | Convert internal dict workaround to typed Pydantic dot-notation |
| L247 | `p_copy` | `'images'` | `p_copy.get("images")[0] if p_copy.get("images") else None` | Convert internal dict workaround to typed Pydantic dot-notation |
| L172 | `user_doc` | `'address'` | `addr = user_doc.get("address") or {}` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L247 | `p_copy` | `'images'` | `p_copy.get("images")[0] if p_copy.get("images") else None` | Convert internal dict workaround to typed Pydantic dot-notation |
| L173 | `addr` | `'city'` | `resolved_city = (addr.get("city") or "").strip() or None` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_recommendation_metrics` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L296 | `doc.meta or {}` | `'slot', 'unknown'` | `slot = (doc.meta or {}).get("slot", "unknown")` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `track_recommendation_event` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L363 | `config.get('section_wise_weights') or {}` | `body.slot` | `section_weights = (config.get("section_wise_weights") or {}).get(body.sl...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L363 | `config` | `'engagement_weights', {}` | `section_weights = (config.get("section_wise_weights") or {}).get(body.sl...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L367 | `section_weights` | `'add_to_cart', 3` | `section_weights.get("add_to_cart", 3)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L369 | `section_weights` | `'product_view', 1` | `else section_weights.get("product_view", 1)` | Convert internal dict workaround to typed Pydantic dot-notation |
| L363 | `config` | `'section_wise_weights'` | `section_weights = (config.get("section_wise_weights") or {}).get(body.sl...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_recommendations` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L114 | `user_doc` | `'address'` | `addr = user_doc.get("address") or {}` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L115 | `addr` | `'city'` | `city = (addr.get("city") or "").strip() or None` | Convert internal dict workaround to typed Pydantic dot-notation |

### `referrals.py` (2 Category A calls)

#### Function / Endpoint: `verify_referral_code` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L97 | `referrer` | `'name', 'Another user'` | `"referrerName": referrer.get("name", "Another user"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L86 | `referrer` | `'_id'` | `if str(referrer.get("_id")) == str(current_user.id):` | Convert internal dict workaround to typed Pydantic dot-notation |

### `returns.py` (15 Category A calls)

#### Function / Endpoint: `create_return_request` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L193 | `eligibility` | `'reason'` | `if eligibility.get("reason"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L227 | `eligibility` | `'returnDeliveryCharge', 0` | `"deliveryCharge": eligibility.get("returnDeliveryCharge", 0),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L244 | `created` | `'_id'` | `"returnId": created.get("_id"),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `complete_return` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L366 | `populated_req` | `'user'` | `email = populated_req.get("user", {}).get("email") if populated_req.get(...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L366 | `populated_req.get('user', {})` | `'email'` | `email = populated_req.get("user", {}).get("email") if populated_req.get(...` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L366 | `populated_req` | `'user', {}` | `email = populated_req.get("user", {}).get("email") if populated_req.get(...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `valet_return_response` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L430 | `ret` | `'status'` | `if ret.get("status") != "pending_valet":` | Convert internal dict workaround to typed Pydantic dot-notation |
| L427 | `ret` | `'pendingValetId', ''` | `if str(ret.get("pendingValetId", "")) != str(current_user.id):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L446 | `ret` | `'valetDeclineHistory'` | `history = list(ret.get("valetDeclineHistory") or [])` | Convert internal dict workaround to typed Pydantic dot-notation |
| L448 | `d` | `'valetId'` | `if not any(isinstance(d, dict) and d.get("valetId") == valet_id_str for ...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `check_return_eligibility` (5 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L168 | `shipping_address` | `'state', ''` | `shipping_address.get("state", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L169 | `shipping_address` | `'city', ''` | `shipping_address.get("city", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L170 | `shipping_address` | `'district', ''` | `shipping_address.get("district", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L171 | `shipping_address` | `'zipCode', ''` | `shipping_address.get("zipCode", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L176 | `charge_data` | `'charge', 0` | `delivery_charge = float(charge_data.get("charge", 0))` | Define strict Pydantic request model and access via dot-notation |

### `seller_availability.py` (2 Category A calls)

#### Function / Endpoint: `get_my_availability_windows` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L218 | `d` | `'startAt', ''` | `docs.sort(key=lambda d: d.get("startAt", ""), reverse=True)` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_all_seller_availability` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L237 | `d` | `'startAt', ''` | `enriched.sort(key=lambda d: d.get("startAt", ""), reverse=True)` | Convert internal dict workaround to typed Pydantic dot-notation |

### `seller_requests.py` (1 Category A calls)

#### Function / Endpoint: `populate_request` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L26 | `response` | `'user'` | `response_user = await user_repository.findById(response.get("user"))` | Convert internal dict workaround to typed Pydantic dot-notation |

### `support_tickets.py` (4 Category A calls)

#### Function / Endpoint: `populate_ticket` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L34 | `response` | `'user'` | `response_user = await user_repository.findById(response.get("user"))` | Convert internal dict workaround to typed Pydantic dot-notation |
| L58 | `assigned_to` | `'_id'` | `"_id": assigned_to.get("_id"),` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L59 | `assigned_to` | `'name'` | `"name": assigned_to.get("name"),` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L60 | `assigned_to` | `'email'` | `"email": assigned_to.get("email"),` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |

### `tracking.py` (4 Category A calls)

#### Function / Endpoint: `track_notify_pincode` (4 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L460 | `data` | `'email'` | `user_email = current_user.email if current_user else data.get("email")` | Define strict Pydantic request model and access via dot-notation |
| L465 | `data` | `'productId'` | `"productId": data.get("productId"),` | Define strict Pydantic request model and access via dot-notation |
| L466 | `data` | `'productName'` | `"productName": data.get("productName"),` | Define strict Pydantic request model and access via dot-notation |
| L467 | `data` | `'pincode'` | `"pincode": data.get("pincode"),` | Define strict Pydantic request model and access via dot-notation |

### `users.py` (21 Category A calls)

#### Function / Endpoint: `get_seller_delivery_settings` (7 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L299 | `current_user.seller_permissions or {}` | `'serviceableZoneIds', []` | `current_zone_ids = (current_user.seller_permissions or {}).get("servicea...` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L304 | `z` | `'name', ''` | `"name": z.get("name", ""),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L305 | `z` | `'pincodes', []` | `"pincodes": z.get("pincodes", []),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L306 | `z` | `'defaultCapacity', 10` | `"defaultCapacity": z.get("defaultCapacity", 10),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L308 | `z` | `'customerType', 'retail'` | `"customerType": z.get("customerType", "retail"),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L303 | `z` | `'_id', ''` | `"id": str(z.get("_id", "")),` | Convert internal dict workaround to typed Pydantic dot-notation |
| L307 | `z` | `'urgentDeliveryAvailable', False` | `"urgentDeliveryAvailable": bool(z.get("urgentDeliveryAvailable", False)),` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `request_email_verification` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L537 | `payload` | `'otp'` | `response_data.code = payload.get("otp")` | Define strict Pydantic request model and access via dot-notation |
| L531 | `payload` | `'message', 'Too many verification requests. Please try again later.'` | `detail=payload.get("message", "Too many verification requests. Please tr...` | Define strict Pydantic request model and access via dot-notation |
| L532 | `payload` | `'retry_after_seconds'` | `headers={"Retry-After": str(int(payload.get("retry_after_seconds") or 0))},` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `verify_email` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L557 | `result` | `'valid'` | `if not result.get("valid"):` | Convert internal dict workaround to typed Pydantic dot-notation |
| L558 | `result` | `'message', 'Invalid or expired verification code.'` | `raise HTTPException(status_code=400, detail=result.get("message", "Inval...` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `get_available_valets` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L189 | `av_id` | `'_id'` | `av_id = av_id.get("_id")` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `update_user` (8 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L383 | `update_dict` | `'companyName'` | `update_dict.get("companyName") if "companyName" in update_dict else exis...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L385 | `update_dict` | `'address'` | `final_address = update_dict.get("address") if "address" in update_dict e...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L401 | `update_dict` | `'companyName'` | `update_dict.get("companyName") if "companyName" in update_dict else exis...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L403 | `update_dict` | `'address'` | `final_address = update_dict.get("address") if "address" in update_dict e...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L393 | `final_address` | `'street'` | `if not final_address.get("street") or not str(final_address.get("street"...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L408 | `final_address` | `'street'` | `if not final_address.get("street") or not str(final_address.get("street"...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L393 | `final_address` | `'street'` | `if not final_address.get("street") or not str(final_address.get("street"...` | Convert internal dict workaround to typed Pydantic dot-notation |
| L408 | `final_address` | `'street'` | `if not final_address.get("street") or not str(final_address.get("street"...` | Convert internal dict workaround to typed Pydantic dot-notation |

### `valet_availability.py` (4 Category A calls)

#### Function / Endpoint: `validate_slots` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L60 | `info.data` | `'availabilityType'` | `availability_type = info.data.get("availabilityType")` | Define strict Pydantic request model and access via dot-notation |

#### Function / Endpoint: `get_all_availability` (2 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L202 | `current_user.seller_permissions or {}` | `'serviceableZoneIds'` | `zone_ids = (current_user.seller_permissions or {}).get("serviceableZoneI...` | Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`) |
| L227 | `d` | `'date', ''` | `enriched.sort(key=lambda d: d.get("date", ""))` | Convert internal dict workaround to typed Pydantic dot-notation |

#### Function / Endpoint: `mark_availability` (1 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L110 | `config` | `'slots', []` | `for slot in config.get("slots", [])` | Convert internal dict workaround to typed Pydantic dot-notation |

### `valet_payout.py` (3 Category A calls)

#### Function / Endpoint: `update_valet_payout_settings` (3 calls)

| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |
|:----:|--------|------|--------------|-------------------------------|
| L76 | `updated` | `'deliveryChargePerOrder', 0.0` | `"deliveryChargePerOrder": updated.get("deliveryChargePerOrder", 0.0),` | Access updated entity model attributes with dot-notation |
| L77 | `updated` | `'returnPickupChargePerOrder', 0.0` | `"returnPickupChargePerOrder": updated.get("returnPickupChargePerOrder", ...` | Access updated entity model attributes with dot-notation |
| L78 | `updated` | `'updatedAt'` | `"updatedAt": updated.get("updatedAt"),` | Access updated entity model attributes with dot-notation |

---

## 4. Comprehensive Breakdown of Category B (Exempt Usages)

Category B encompasses legitimate usages where dictionary `.get()` or method `.get()` is appropriate and exempt from Pydantic model refactoring:

### 4.1 FastAPI Route Decorators (`@router.get` / `app.get`)
- **Total Count**: 247 instances across 53 router files.
- **Rationale**: Standard FastAPI route registration decorator (e.g., `@router.get('/summary')`). It is not a dictionary method call.

### 4.2 HTTP Request Headers & Query Parameters
- **Total Count**: 3 instances
  - `activity.py:17`: `request.headers.get('authorization')`
  - `activity.py:51`: `request.headers.get('x-session-id')`
  - `recommendations.py:334`: `request.headers.get('x-session-id')`
- **Rationale**: Standard Starlette / FastAPI `Request.headers` mapping lookup explicitly exempted by R1.

### 4.3 Database Repository Singleton Fetch Methods
- **Total Count**: 5 instances
  - `content_pages.py:139`: `doc = await about_repository.get()`
  - `content_pages.py:145`: `doc = await about_repository.get()`
  - `content_pages.py:162`: `doc = await privacy_repository.get()`
  - `content_pages.py:168`: `doc = await privacy_repository.get()`
  - `content_pages.py:187`: `doc = await privacy_repository.get()`
- **Rationale**: Calling the async zero-argument repository method `repo.get()` to fetch the singleton document.

### 4.4 In-Memory Dynamic Hash Tables, ID Maps & Caches
- **Total Count**: 20 instances across 9 files
  - `bundles.py:232`: `product_map.get(str(pid))`
  - `cart.py:58`: `products_map.get(str(item.product))`
  - `orders.py:224`: `users_map.get(o_user_id)`
  - `orders.py:227`: `users_map.get(o_valet_id)`
  - `orders.py:230`: `payments_map.get(o_id, [])`
  - `orders.py:244`: `products_map.get(prod_id)`
  - `orders.py:511`: `_cart_products_map.get(str(item.product or item.product_id))`
  - `orders.py:631`: `_cart_products_map.get(str(item.product or item.product_id))`
  - `orders.py:1519`: `seller_delivery_map.get(str(seller_id) if seller_id else None)`
  - `orders.py:1540`: `seller_docs.get(str(seller_id))`
  - `payments.py:217`: `order_map.get(str(payment.order_id))`
  - `recommendations.py:91, 97`: `_guest_rec_cache.get(guest_key)`
  - `recommendations.py:122`: `cache.get(user_cache_key)`
  - `recommendations.py:204, 224`: `product_map.get(pid)`
  - `seller_availability.py:141`: `sellers_map.get(sid, {})`
  - `users.py:168`: `avail_map.get(vid)`
  - `valet_availability.py:208`: `valets_map.get(vid, {})`
  - `wishlist.py:64`: `products_map.get(str(item.product))`
- **Rationale**: Dynamic key lookups in in-memory hash maps (`Dict[str, T]`) constructed for O(1) bulk joins.

### 4.5 In-Memory Tally Frequency Counters
- **Total Count**: 2 instances
  - `returns.py:132`: `returned_items_qty[pid] = returned_items_qty.get(pid, 0) + ...`
  - `returns.py:148`: `returned_qty = returned_items_qty.get(pid, 0)`
- **Rationale**: Standard Python integer accumulator counter pattern (`Dict[str, int]`).

### 4.6 Static Platform Config Mapping
- **Total Count**: 1 instance
  - `version.py:37`: `min_for_platform = min_versions.get(platform_key, config.MIN_APP_VERSION_WEB)`
- **Rationale**: Dynamic platform key lookup in a localized dictionary mapping ('ios'|'android'|'web').

---

## 5. Refactoring Blueprint & Migration Guide for Implementation

To achieve full compliance with R1, R2, and R3 following the pattern in `ads.py`:

1. **Request Payload Modernization**:
   - `analytics.py`: Replace generic `event: Dict[str, Any]` with `AnalyticsEventPayload(BaseModel)` containing typed fields (`type: str`, `session_id: Optional[str]`, `payload: Optional[Dict[str, Any]]`).
   - `tracking.py`: Replace `data: dict` in `/notify-pincode` with `NotifyPincodePayload(BaseModel)` (`productId: str`, `productName: str`, `pincode: str`, `email: Optional[str]`).
   - `auth.py`: Replace webhook/dict payload extraction with typed models.

2. **Entity & Model Dot-Notation Enforcment**:
   - `orders.py`: Access `order_data.shippingAddress.state` instead of `order_data.shippingAddress.get('state')`.
   - `delivery_slots.py`: Convert internal slot dictionaries to `DeliverySlot` model instances and use `slot.id`, `slot.capacity`, `slot.booked_count`.
   - `products.py`: Access CSV model attributes directly (`main_row.quantity_per_case`, `main_row.sku`).
   - `payments.py`: Replace `entry.get('amount')` with `entry.amount` and `entry.verified`.
   - `support_tickets.py` & `seller_requests.py`: Access user fields directly (`assigned_to.id`, `assigned_to.name`).

