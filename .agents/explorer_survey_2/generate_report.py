import json
import os

with open("c:/Ecommerce app/.agents/explorer_survey_2/classified_calls.json", "r", encoding="utf-8") as f:
    classified_calls = json.load(f)

routers_dir = r"backend/app/routers"
all_py_files = sorted([f for f in os.listdir(routers_dir) if f.endswith('.py')])

# Add backup / tmp files
extra_files = ["analytics.py.tmp", "orders.py.bak"]

by_file = {}
for fname in all_py_files:
    by_file[fname] = []

for c in classified_calls:
    by_file.setdefault(c["file"], []).append(c)

report_path = r"c:/Ecommerce app/.agents/explorer_survey_2/survey_report.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write("# Router `.get(` Scanner Survey Report\n\n")
    f.write("**Explorer**: Explorer 2 (Router Get Scanner Explorer)\n")
    f.write("**Date**: 2026-09-13\n")
    f.write("**Scope**: All router files in `backend/app/routers/`\n")
    f.write("**Reference Standard**: Pattern established in `backend/app/routers/ads.py`\n\n")
    f.write("---\n\n")

    # Executive Summary
    total_calls = len(classified_calls)
    total_cat_a = sum(1 for c in classified_calls if c["category"] == "Category A")
    total_cat_b = sum(1 for c in classified_calls if c["category"] == "Category B")
    total_route = sum(1 for c in classified_calls if c["caller"] in ("router", "app"))
    total_other_b = total_cat_b - total_route
    files_with_cat_a = sum(1 for fname, calls in by_file.items() if any(c["category"] == "Category A" for c in calls))
    files_clean = len(all_py_files) - files_with_cat_a

    f.write("## 1. Executive Summary\n\n")
    f.write("A complete static and AST analysis was executed across all router files in `backend/app/routers/` to identify, analyze, and categorize every instance of `.get(`.\n\n")
    f.write(f"- **Total Active Python Router Files**: {len(all_py_files)} (including `__init__.py`)\n")
    f.write(f"- **Additional Tracked Router Files**: {len(extra_files)} (`analytics.py.tmp`, `orders.py.bak`)\n")
    f.write(f"- **Total Router Files Tracked in Repository**: {len(all_py_files) + len(extra_files)} (57 total files)\n")
    f.write(f"- **Total `.get(` Instances in Active Routers**: {total_calls}\n")
    f.write(f"- **Category A (Dict Workarounds to Refactor)**: **{total_cat_a} calls** across **{files_with_cat_a} files**\n")
    f.write(f"- **Category B (Exempt Usages)**: **{total_cat_b} calls** across {len(all_py_files)} files\n")
    f.write(f"  - *FastAPI `@router.get` route decorators*: {total_route} calls\n")
    f.write(f"  - *Exempt Standard Dict / Headers / Cache / DB Repository lookups*: {total_other_b} calls\n")
    f.write(f"- **Files Completely Clean of Category A**: **{files_clean} active router files**\n\n")
    f.write("---\n\n")

    # Complete Inventory Table
    f.write("## 2. Complete Inventory Table (All 55 Active Routers + 2 Legacy Files)\n\n")
    f.write("| # | Router File | Cat A (Dict Workarounds) | Cat B (Exempt) | Route Decorators (`@router.get`) | Total `.get(` Calls | Status |\n")
    f.write("|---|-------------|:------------------------:|:--------------:|:--------------------------------:|:-------------------:|:------:|\n")

    idx = 1
    for fname in all_py_files:
        fcalls = by_file.get(fname, [])
        ca = sum(1 for c in fcalls if c["category"] == "Category A")
        cb = sum(1 for c in fcalls if c["category"] == "Category B")
        cr = sum(1 for c in fcalls if c["caller"] in ("router", "app"))
        cb_other = cb - cr
        tot = len(fcalls)
        status = "⚠️ Needs Refactor" if ca > 0 else "✅ Clean"
        f.write(f"| {idx} | `{fname}` | **{ca}** | {cb_other} | {cr} | {tot} | {status} |\n")
        idx += 1

    f.write(f"| 56 | `analytics.py.tmp` (legacy temp file) | 1 | 0 | 0 | 1 | ⚠️ Legacy Temp |\n")
    f.write(f"| 57 | `orders.py.bak` (pre-refactor backup) | 479 | 0 | 0 | 479 | ⚠️ Legacy Backup |\n")
    f.write(f"| | **Active Routers Total (55 files)** | **{total_cat_a}** | **{total_other_b}** | **{total_route}** | **{total_calls}** | |\n\n")

    f.write("---\n\n")

    # Detailed Category A Breakdown
    f.write("## 3. Detailed Category A Inventory (Files Requiring Refactoring)\n\n")
    f.write("Each entry lists the file, line number, enclosing function/endpoint, code snippet, and the specific refactoring action required.\n\n")

    for fname in all_py_files:
        fcalls = by_file.get(fname, [])
        cat_a_calls = [c for c in fcalls if c["category"] == "Category A"]
        if not cat_a_calls:
            continue

        f.write(f"### `{fname}` ({len(cat_a_calls)} Category A calls)\n\n")
        
        # Group by function
        funcs = {}
        for c in cat_a_calls:
            funcs.setdefault(c["func"], []).append(c)

        for fn, fn_calls in funcs.items():
            f.write(f"#### Function / Endpoint: `{fn}` ({len(fn_calls)} calls)\n\n")
            f.write("| Line | Caller | Args | Code Snippet | Required Pydantic Refactoring |\n")
            f.write("|:----:|--------|------|--------------|-------------------------------|\n")
            for c in fn_calls:
                line = c["lineno"]
                caller = f"`{c['caller']}`"
                args = f"`{c['args']}`"
                # Clean snippet for markdown table
                snippet = c["line_str"].replace("|", "\\|")
                if len(snippet) > 75:
                    snippet = snippet[:72] + "..."
                code_cell = f"`{snippet}`"
                
                # Contextual recommendation
                if "order_data.shippingAddress" in c["caller"]:
                    recom = "Replace with `order_data.shippingAddress.<field>` via `ShippingAddress` model"
                elif "slot" in c["caller"] or "sl" in c["caller"]:
                    recom = "Replace with `DeliverySlot` model dot-notation (e.g. `slot.id`, `slot.start_time`)"
                elif "payload" in c["caller"] or "data" in c["caller"]:
                    recom = "Define strict Pydantic request model and access via dot-notation"
                elif "validation" in c["caller"] or "coupon" in c["caller"]:
                    recom = "Replace with `CouponValidationResult` model dot-notation"
                elif "main_row" in c["caller"] or "row" in c["caller"]:
                    recom = "Access Pydantic `CsvProductRow` model attributes directly"
                elif "user" in c["caller"] or "assigned_to" in c["caller"] or "seller_doc" in c["caller"]:
                    recom = "Access `User` model attributes (e.g. `user.id`, `user.name`, `user.email`)"
                elif "entry" in c["caller"]:
                    recom = "Access `PaymentEntry` model attributes (e.g. `entry.amount`, `entry.verified`)"
                elif "updated" in c["caller"]:
                    recom = "Access updated entity model attributes with dot-notation"
                else:
                    recom = "Convert internal dict workaround to typed Pydantic dot-notation"

                f.write(f"| L{line} | {caller} | {args} | {code_cell} | {recom} |\n")
            f.write("\n")

    f.write("---\n\n")

    # Detailed Category B Breakdown
    f.write("## 4. Comprehensive Breakdown of Category B (Exempt Usages)\n\n")
    f.write("Category B encompasses legitimate usages where dictionary `.get()` or method `.get()` is appropriate and exempt from Pydantic model refactoring:\n\n")
    
    f.write("### 4.1 FastAPI Route Decorators (`@router.get` / `app.get`)\n")
    f.write(f"- **Total Count**: {total_route} instances across 53 router files.\n")
    f.write("- **Rationale**: Standard FastAPI route registration decorator (e.g., `@router.get('/summary')`). It is not a dictionary method call.\n\n")

    f.write("### 4.2 HTTP Request Headers & Query Parameters\n")
    f.write("- **Total Count**: 3 instances\n")
    f.write("  - `activity.py:17`: `request.headers.get('authorization')`\n")
    f.write("  - `activity.py:51`: `request.headers.get('x-session-id')`\n")
    f.write("  - `recommendations.py:334`: `request.headers.get('x-session-id')`\n")
    f.write("- **Rationale**: Standard Starlette / FastAPI `Request.headers` mapping lookup explicitly exempted by R1.\n\n")

    f.write("### 4.3 Database Repository Singleton Fetch Methods\n")
    f.write("- **Total Count**: 5 instances\n")
    f.write("  - `content_pages.py:139`: `doc = await about_repository.get()`\n")
    f.write("  - `content_pages.py:145`: `doc = await about_repository.get()`\n")
    f.write("  - `content_pages.py:162`: `doc = await privacy_repository.get()`\n")
    f.write("  - `content_pages.py:168`: `doc = await privacy_repository.get()`\n")
    f.write("  - `content_pages.py:187`: `doc = await privacy_repository.get()`\n")
    f.write("- **Rationale**: Calling the async zero-argument repository method `repo.get()` to fetch the singleton document.\n\n")

    f.write("### 4.4 In-Memory Dynamic Hash Tables, ID Maps & Caches\n")
    f.write("- **Total Count**: 20 instances across 9 files\n")
    f.write("  - `bundles.py:232`: `product_map.get(str(pid))`\n")
    f.write("  - `cart.py:58`: `products_map.get(str(item.product))`\n")
    f.write("  - `orders.py:224`: `users_map.get(o_user_id)`\n")
    f.write("  - `orders.py:227`: `users_map.get(o_valet_id)`\n")
    f.write("  - `orders.py:230`: `payments_map.get(o_id, [])`\n")
    f.write("  - `orders.py:244`: `products_map.get(prod_id)`\n")
    f.write("  - `orders.py:511`: `_cart_products_map.get(str(item.product or item.product_id))`\n")
    f.write("  - `orders.py:631`: `_cart_products_map.get(str(item.product or item.product_id))`\n")
    f.write("  - `orders.py:1519`: `seller_delivery_map.get(str(seller_id) if seller_id else None)`\n")
    f.write("  - `orders.py:1540`: `seller_docs.get(str(seller_id))`\n")
    f.write("  - `payments.py:217`: `order_map.get(str(payment.order_id))`\n")
    f.write("  - `recommendations.py:91, 97`: `_guest_rec_cache.get(guest_key)`\n")
    f.write("  - `recommendations.py:122`: `cache.get(user_cache_key)`\n")
    f.write("  - `recommendations.py:204, 224`: `product_map.get(pid)`\n")
    f.write("  - `seller_availability.py:141`: `sellers_map.get(sid, {})`\n")
    f.write("  - `users.py:168`: `avail_map.get(vid)`\n")
    f.write("  - `valet_availability.py:208`: `valets_map.get(vid, {})`\n")
    f.write("  - `wishlist.py:64`: `products_map.get(str(item.product))`\n")
    f.write("- **Rationale**: Dynamic key lookups in in-memory hash maps (`Dict[str, T]`) constructed for O(1) bulk joins.\n\n")

    f.write("### 4.5 In-Memory Tally Frequency Counters\n")
    f.write("- **Total Count**: 2 instances\n")
    f.write("  - `returns.py:132`: `returned_items_qty[pid] = returned_items_qty.get(pid, 0) + ...`\n")
    f.write("  - `returns.py:148`: `returned_qty = returned_items_qty.get(pid, 0)`\n")
    f.write("- **Rationale**: Standard Python integer accumulator counter pattern (`Dict[str, int]`).\n\n")

    f.write("### 4.6 Static Platform Config Mapping\n")
    f.write("- **Total Count**: 1 instance\n")
    f.write("  - `version.py:37`: `min_for_platform = min_versions.get(platform_key, config.MIN_APP_VERSION_WEB)`\n")
    f.write("- **Rationale**: Dynamic platform key lookup in a localized dictionary mapping ('ios'|'android'|'web').\n\n")

    f.write("---\n\n")

    # Refactoring Blueprint
    f.write("## 5. Refactoring Blueprint & Migration Guide for Implementation\n\n")
    f.write("To achieve full compliance with R1, R2, and R3 following the pattern in `ads.py`:\n\n")
    f.write("1. **Request Payload Modernization**:\n")
    f.write("   - `analytics.py`: Replace generic `event: Dict[str, Any]` with `AnalyticsEventPayload(BaseModel)` containing typed fields (`type: str`, `session_id: Optional[str]`, `payload: Optional[Dict[str, Any]]`).\n")
    f.write("   - `tracking.py`: Replace `data: dict` in `/notify-pincode` with `NotifyPincodePayload(BaseModel)` (`productId: str`, `productName: str`, `pincode: str`, `email: Optional[str]`).\n")
    f.write("   - `auth.py`: Replace webhook/dict payload extraction with typed models.\n\n")
    f.write("2. **Entity & Model Dot-Notation Enforcment**:\n")
    f.write("   - `orders.py`: Access `order_data.shippingAddress.state` instead of `order_data.shippingAddress.get('state')`.\n")
    f.write("   - `delivery_slots.py`: Convert internal slot dictionaries to `DeliverySlot` model instances and use `slot.id`, `slot.capacity`, `slot.booked_count`.\n")
    f.write("   - `products.py`: Access CSV model attributes directly (`main_row.quantity_per_case`, `main_row.sku`).\n")
    f.write("   - `payments.py`: Replace `entry.get('amount')` with `entry.amount` and `entry.verified`.\n")
    f.write("   - `support_tickets.py` & `seller_requests.py`: Access user fields directly (`assigned_to.id`, `assigned_to.name`).\n\n")

print("Report generated successfully!")
