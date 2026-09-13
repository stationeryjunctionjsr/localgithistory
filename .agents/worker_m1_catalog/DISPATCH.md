# Dispatch — Worker M1 Catalog (worker_m1_catalog)

## 2026-09-13T19:01:00+05:30

### Working Directory
`c:\Ecommerce app\.agents\worker_m1_catalog`

### Exclusive Write Ownership
- `backend/app/routers/products.py`
- `backend/app/routers/returns.py`
- `backend/app/routers/order_feedback.py`
(Exclusively owned by this worker. No other worker will touch these files.)

### Objective
Eliminate all Category A `.get()` calls across `products.py` (36 calls), `returns.py` (15 calls), and `order_feedback.py` (4 calls) by transitioning to strict Pydantic models and dot notation per the reference pattern established in `backend/app/routers/ads.py`.

### Mandatory Documents to Read First
- `c:\Ecommerce app\.agents\ORIGINAL_REQUEST.md`
- `c:\Ecommerce app\PROJECT.md`
- `c:\Ecommerce app\.agents\explorer_survey_1\survey_report.md` (ads.py reference pattern)
- `c:\Ecommerce app\.agents\explorer_survey_2\survey_report.md` (Sections for products.py, returns.py, order_feedback.py)

### Specific Instructions
1. **`backend/app/routers/products.py`** (36 Category A calls):
   - Replace dictionary workarounds on product objects, `main_row`, and related entities with direct dot notation.
   - For optional attributes, use ternary fallbacks (`x.field if x.field is not None else default`).
2. **`backend/app/routers/returns.py`** (15 Category A calls):
   - Replace dictionary workarounds on `shipping_address`, `return_request`, and return payloads with direct dot notation.
3. **`backend/app/routers/order_feedback.py`** (4 Category A calls):
   - Replace `latest_eligible_order.get("_id")` -> `latest_eligible_order.id` (or `latest_eligible_order._id`)
   - Replace `feedback.get("orderId")` -> `feedback.order_id` / `feedback.orderId`
   - Replace `latest_feedback.get("createdAt")` -> `latest_feedback.created_at` / `latest_feedback.createdAt`
4. **Preserve Standard Category B Usages**:
   - `@router.get` decorators are preserved.
5. **Zero Category A Calls**:
   - Ensure all 3 files have 0 Category A `.get()` calls remaining.

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Verification Commands (to run from `c:\Ecommerce app\backend`)
1. `python -c "import importlib; [importlib.import_module(f'app.routers.{m}') for m in ['products', 'returns', 'order_feedback']]; print('All 3 routers loaded cleanly')"`
2. `python -c "from app.main import app; schema = app.openapi(); print('OpenAPI paths:', len(schema['paths']))"`
3. Verify zero Category A calls in `products.py`, `returns.py`, and `order_feedback.py`.

### Deliverables
Write `handoff.md` and `progress.md` in `c:\Ecommerce app\.agents\worker_m1_catalog\` and send completion message to orchestrator_2.
