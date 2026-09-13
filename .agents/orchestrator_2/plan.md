# Plan — Router Pydantic Refactoring Execution

## Objective
Aggressively execute Milestones M0 through M5 to eliminate all Category A dictionary workarounds across the FastAPI codebase, enforce Pydantic dot notation, and pass full verification.

## Milestone Breakdown & Execution Strategy

### Milestone M0: Core Foundation & Shared Schemas
- **Scope**: `backend/app/models/schemas.py`, `backend/app/models/user.py`
- **Actions**:
  1. Add missing `CartItem`, `OrderItem`, `VisibilityRule`, `SellerPermissions` exports/aliases and `AdSummaryResponse` in `schemas.py`.
  2. Define shared request models (`AnalyticsEventCreate`, `Msg91WebhookPayload`, `TrackBeaconRequest`, `TrackNotifyPincodeRequest`, `SellerDeliveryOption`, `OrderItemCreate`, `PushSubscription`, `DeliveryChargeTier`).
  3. Ensure `user.py` cleanly imports from `schemas.py`.
  4. Verify that `python -c "import app.main; print('App Main Import Succeeded!')"` passes.
- **Workers**: Worker `worker_m0` -> Reviewer -> Auditor gate.

### Milestone M1: Core E-Commerce & Ordering
- **Scope**: `backend/app/routers/orders.py`, `products.py`, `returns.py`, `order_feedback.py`
- **Actions**:
  1. Refactor `orders.py` (134 calls): Update `OrderCreateRequest` to typed models (`shippingAddress: Address`, `items: List[OrderItemCreate]`, etc.), replace `.get()` on payloads and query/dict results with dot notation and null checks.
  2. Refactor `products.py` (36 calls): Update `main_row`, `product_doc` access.
  3. Refactor `returns.py` (15 calls): Update `shipping_address`, `return_request` access.
  4. Refactor `order_feedback.py` (4 calls): Update `latest_eligible_order`, `latest_feedback` access.
- **Verification**: Single-router imports + pytest test pass.

### Milestone M2: Delivery & Logistics
- **Scope**: `backend/app/routers/delivery_slots.py`, `delivery_charges.py`, `delivery_zones.py`, `valet_availability.py`, `valet_payout.py`, `tracking.py`
- **Actions**:
  1. Refactor `delivery_slots.py` (55 calls): Typed slot/config dot notation.
  2. Refactor `delivery_charges.py` (7 calls): Typed `DeliveryChargeTier`, seller doc dot notation.
  3. Refactor `delivery_zones.py` (2 calls): Zone pincode/name access.
  4. Refactor `valet_availability.py` (4 calls) and `valet_payout.py` (3 calls).
  5. Refactor `tracking.py` (4 calls): Replace untyped `/beacon` and `/notify-pincode` bodies with typed models.
- **Verification**: Single-router imports + pytest test pass.

### Milestone M3: Identity, Analytics & User Interactions
- **Scope**: `backend/app/routers/analytics.py`, `users.py`, `auth.py`, `recommendations.py`, `push_notifications.py`, `referrals.py`
- **Actions**:
  1. Refactor `analytics.py` (24 calls): Use `AnalyticsEventCreate` for `/events` and dot notation.
  2. Refactor `users.py` (21 calls): User doc / profile dot notation.
  3. Refactor `auth.py` (17 calls): Use `Msg91WebhookPayload`, OTP verification dot notation.
  4. Refactor `recommendations.py` (13 calls): Recommendations model access.
  5. Refactor `push_notifications.py` (8 calls): Use `DeviceRegistrationRequest` with `PushSubscription`.
  6. Refactor `referrals.py` (2 calls): Referral code and user access.
- **Verification**: Single-router imports + pytest test pass.

### Milestone M4: Merchant, Financial & Content Operations
- **Scope**: `commission.py`, `availability_requests.py`, `payments.py`, `page_info.py`, `support_tickets.py`, `content_pages.py`, `seller_availability.py`, `category_tags.py`, `feature_flags.py`, `seller_requests.py`, and remove `analytics.py.tmp`, `orders.py.bak`
- **Actions**:
  1. Refactor `commission.py` (9 calls): Use Pydantic dot notation for `CommissionTier`.
  2. Refactor `availability_requests.py` (7 calls) & `seller_requests.py` (1 call).
  3. Refactor `payments.py` (6 calls) & `support_tickets.py` (4 calls).
  4. Refactor `page_info.py` (5 calls), `content_pages.py` (2 calls), `seller_availability.py` (2 calls), `category_tags.py` (1 call), `feature_flags.py` (1 call).
  5. Purge `analytics.py.tmp` and `orders.py.bak`.
- **Verification**: Single-router imports + pytest test pass.

### Milestone M5: Global Acceptance Verification
- **Scope**: Entire `backend/app/routers/` + App Startup + Pytest Suite
- **Actions**:
  1. Comprehensive scan for `.get(` across all 56 router files confirming 0 Category A instances remain.
  2. App startup test: `python -c "import app.main; print('Success')"`.
  3. Pytest health test: `python -m pytest tests/test_health.py`.
  4. Dispatch Forensic Auditor for integrity verification.
  5. Send completion report to Sentinel via `send_message`.
