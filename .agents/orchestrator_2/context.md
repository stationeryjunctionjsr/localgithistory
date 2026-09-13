# Context & Environment — Orchestrator 2

## Project Context
- **Workspace**: `c:\Ecommerce app`
- **Subsystem**: `backend/app/routers/` (55 active routers, 387 Category A `.get()` calls to eliminate)
- **Central Schema Store**: `backend/app/models/schemas.py`
- **Reference Standard**: `backend/app/routers/ads.py`
- **Python Runtime**: Python 3.14.2 / Windows
- **FastAPI / Pydantic**: FastAPI 0.141.1, Pydantic v2 (2.12.5)

## Survey Discoveries Summary
1. `explorer_survey_1`:
   - Reference pattern in `ads.py`: typed route payloads, dot notation (`payload.field`), ternary fallbacks (`x if x is not None else default`), `.model_dump()` for storage updates.
   - Identified missing `AdSummaryResponse` and alias imports in `schemas.py` / `user.py`.
2. `explorer_survey_2`:
   - 387 Category A calls across 26 router files.
   - 29 router files already clean of Category A.
   - Legacy files: `analytics.py.tmp` and `orders.py.bak` to be cleaned.
3. `explorer_survey_3`:
   - 4 direct dict/untyped request body endpoints:
     - `analytics.py`: `POST /events`
     - `auth.py`: `POST /msg91-webhook`
     - `tracking.py`: `POST /beacon`
     - `tracking.py`: `POST /notify-pincode`
   - Request models with embedded dict fields:
     - `OrderCreateRequest` in `orders.py` (`shippingAddress`, `billingAddress`, `items`, `sellerDeliveryOptions`)
     - `DeviceRegistrationRequest` in `push_notifications.py` (`subscription`)
     - `DeliveryChargeBase` in `schemas.py` (`tiers`)
   - `commission.py`: Pydantic model accessed with `.get()` workarounds.
   - Root cause of initial import failure: `CartItem` missing in `schemas.py` when imported by `user.py:1`.

## Dependency & Milestone Layout
- **M0**: Core Foundation & Shared Schemas (`backend/app/models/schemas.py`, `backend/app/models/user.py`)
- **M1**: Core E-Commerce & Ordering (`orders.py`, `products.py`, `returns.py`, `order_feedback.py`)
- **M2**: Delivery & Logistics (`delivery_slots.py`, `delivery_charges.py`, `delivery_zones.py`, `valet_availability.py`, `valet_payout.py`, `tracking.py`)
- **M3**: Identity, Analytics & User Interactions (`analytics.py`, `users.py`, `auth.py`, `recommendations.py`, `push_notifications.py`, `referrals.py`)
- **M4**: Merchant, Financial & Content Operations (`commission.py`, `availability_requests.py`, `payments.py`, `page_info.py`, `support_tickets.py`, `content_pages.py`, `seller_availability.py`, `category_tags.py`, `feature_flags.py`, `seller_requests.py`, and remove `analytics.py.tmp`, `orders.py.bak`)
- **M5**: Global Acceptance & Test Verification (all 56 router files Category A clean, app startup pass, pytest test verification)
