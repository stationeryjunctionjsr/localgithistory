# Dispatch — Worker M1 Orders (worker_m1_orders)

## 2026-09-13T19:01:00+05:30

### Working Directory
`c:\Ecommerce app\.agents\worker_m1_orders`

### Exclusive Write Ownership
- `backend/app/routers/orders.py` (Exclusively owned by this worker. No other worker will touch this file.)

### Objective
Eliminate all 134 Category A `.get()` dictionary workaround calls in `backend/app/routers/orders.py` by transitioning request payloads and internal data structures to strict Pydantic models and dot notation per the reference pattern established in `backend/app/routers/ads.py`.

### Mandatory Documents to Read First
- `c:\Ecommerce app\.agents\ORIGINAL_REQUEST.md`
- `c:\Ecommerce app\PROJECT.md`
- `c:\Ecommerce app\.agents\explorer_survey_1\survey_report.md` (ads.py reference pattern)
- `c:\Ecommerce app\.agents\explorer_survey_2\survey_report.md` (lines 376–448: complete list of all 134 Category A calls in `orders.py`)
- `c:\Ecommerce app\.agents\explorer_survey_3\survey_report.md` (§3 Model 1: `OrderCreateRequest` analysis)

### Specific Instructions for `orders.py`
1. **Update `OrderCreateRequest`** (around line 112):
   - `shippingAddress: Address` (imported from `app.models.schemas`)
   - `billingAddress: Optional[Address] = None`
   - `items: Optional[List[OrderItemCreate]] = None` (imported from `app.models.schemas`)
   - `sellerDeliveryOptions: Optional[List[SellerDeliveryOption]] = None` (imported from `app.models.schemas`)
2. **Refactor Address Access**:
   - Replace all `order_data.shippingAddress.get("zipCode")`, `.get("state")`, `.get("city")`, `.get("district")` with direct dot notation and null safety:
     `order_data.shippingAddress.zipCode if order_data.shippingAddress else ""` (etc.)
3. **Refactor Delivery Slot & Config Access**:
   - Replace `.get("slots")`, `.get("capacity")`, `.get("bookedCount")`, `.get("isUrgent")`, `.get("isFullDay")`, `.get("startTime")`, `.get("endTime")` with typed model dot notation.
4. **Refactor Coupon & Discount Validation**:
   - Replace `validation.get("valid")`, `validation.get("coupon")`, `validation.get("itemDiscounts")`, etc. with typed dot notation or Pydantic models.
5. **Preserve Standard Exemptions (Category B)**:
   - `@router.get` decorators are preserved.
   - Standard dictionary lookups on in-memory maps (e.g. `users_map.get(uid)`) are exempt.
6. **Zero Category A Calls**:
   - Every single `.get()` on request payloads, coupon objects, shipping addresses, and slot data must be eliminated.

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Verification Commands (to run from `c:\Ecommerce app\backend`)
1. `python -c "import importlib; importlib.import_module('app.routers.orders'); print('orders router loaded cleanly')"`
2. `python -c "from app.main import app; schema = app.openapi(); print('OpenAPI paths:', len(schema['paths']))"`
3. Verify zero Category A calls in `orders.py`.

### Deliverables
Write `handoff.md` and `progress.md` in `c:\Ecommerce app\.agents\worker_m1_orders\` and send completion message to orchestrator_2.

## 2026-09-13T13:43:09Z
**Context**: Milestone M1 orders.py refactoring progress check
**Content**: Worker catalog has completed its refactoring of products, returns, and order_feedback. Please provide a brief status update on your refactoring of orders.py and your current progress.
**Action**: Reply with current status or finish remaining steps and submit handoff.md.

## 2026-09-13T16:00:12Z
You are worker_m1_orders, assigned to Milestone M1 (Orders Router Refactoring).
Working directory: c:\Ecommerce app\.agents\worker_m1_orders
Read c:\Ecommerce app\.agents\worker_m1_orders\DISPATCH.md, c:\Ecommerce app\.agents\ORIGINAL_REQUEST.md, and c:\Ecommerce app\.agents\explorer_survey_2\survey_report.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Eliminate all Category A .get() calls in backend/app/routers/orders.py using Pydantic models (OrderCreateRequest, Address, OrderItemCreate, SellerDeliveryOption, DeliverySlot, etc.) and dot notation with null-safe ternary fallbacks.
Preserve Category B usages (@router.get decorators and in-memory map .get()).
Verify with:
python -c "import importlib; importlib.import_module('app.routers.orders'); print('orders loaded cleanly')"
and app.openapi().
Write handoff.md and send completion message back to orchestrator_2.
