# Project: Router Pydantic Refactoring & Dictionary Workaround Elimination

## Architecture
- **Framework**: FastAPI with Pydantic v2 (FastAPI 0.141.1, Python 3.14.2)
- **Target Subsystem**: `backend/app/routers/*.py` (55 active router modules + `ads.py` reference)
- **Central Schema Store**: `backend/app/models/schemas.py`
- **Reference Model**: `backend/app/routers/ads.py`
- **Data Flow**:
  1. Incoming HTTP requests parsed and validated by FastAPI via strict Pydantic models in endpoint signatures.
  2. Endpoints access fields via dot notation (e.g. `payload.status`, `event.type`).
  3. Nullable / optional fields use explicit ternary fallbacks (`field if field is not None else default`).
  4. Models serialized to dict via `.model_dump()` when calling underlying storage / repositories.
  5. Zero `.get()` dictionary workarounds on request payloads or internal data structures.

## Code Layout
- `backend/app/routers/ads.py`: Gold standard reference implementation.
- `backend/app/models/schemas.py`: Shared Pydantic DTOs and entity models.
- `backend/app/routers/*.py`: Route definitions and handlers.
- `backend/app/main.py`: FastAPI app entrypoint and router registration.
- `backend/tests/`: Pytest test suite.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Core Schema Unblocking | Add missing `AdSummaryResponse` and alias imports in `schemas.py` / `user.py` to restore app importability | M0 | ORIGINAL_REQUEST.md & Survey |
| 2 | Shared Pydantic Payload DTOs | Define common payload models in `schemas.py` (`AnalyticsEventCreate`, `Msg91WebhookPayload`, `OrderItemCreate`, `PushSubscription`, etc.) | M0 | ORIGINAL_REQUEST.md §R2 |
| 3 | Orders Router Refactoring | Refactor 134 Category A `.get()` calls in `orders.py` to Pydantic models and dot-notation | M1 | ORIGINAL_REQUEST.md §R1, §R3 |
| 4 | Products Router Refactoring | Refactor 36 Category A `.get()` calls in `products.py` to Pydantic models and dot-notation | M1 | ORIGINAL_REQUEST.md §R1, §R3 |
| 5 | Returns Router Refactoring | Refactor 15 Category A `.get()` calls in `returns.py` to Pydantic models and dot-notation | M1 | ORIGINAL_REQUEST.md §R1, §R3 |
| 6 | Order Feedback Router Refactoring | Refactor 4 Category A `.get()` calls in `order_feedback.py` to Pydantic models and dot-notation | M1 | ORIGINAL_REQUEST.md §R1, §R3 |
| 7 | Delivery Slots Router Refactoring | Refactor 55 Category A `.get()` calls in `delivery_slots.py` to Pydantic models and dot-notation | M2 | ORIGINAL_REQUEST.md §R1, §R3 |
| 8 | Delivery Charges Router Refactoring | Refactor 7 Category A `.get()` calls in `delivery_charges.py` to Pydantic models and dot-notation | M2 | ORIGINAL_REQUEST.md §R1, §R3 |
| 9 | Delivery Zones Router Refactoring | Refactor 2 Category A `.get()` calls in `delivery_zones.py` to Pydantic models and dot-notation | M2 | ORIGINAL_REQUEST.md §R1, §R3 |
| 10 | Valet Operations Router Refactoring | Refactor 7 Category A `.get()` calls across `valet_availability.py` and `valet_payout.py` | M2 | ORIGINAL_REQUEST.md §R1, §R3 |
| 11 | Tracking Router Refactoring | Refactor 4 Category A `.get()` calls and typed payloads (`/beacon`, `/notify-pincode`) in `tracking.py` | M2 | ORIGINAL_REQUEST.md §R1-§R3 |
| 12 | Analytics Router Refactoring | Refactor 24 Category A `.get()` calls and `/events` payload in `analytics.py` | M3 | ORIGINAL_REQUEST.md §R1-§R3 |
| 13 | Users Router Refactoring | Refactor 21 Category A `.get()` calls in `users.py` to Pydantic models and dot-notation | M3 | ORIGINAL_REQUEST.md §R1, §R3 |
| 14 | Auth Router Refactoring | Refactor 17 Category A `.get()` calls and `/msg91-webhook` payload in `auth.py` | M3 | ORIGINAL_REQUEST.md §R1-§R3 |
| 15 | Recommendations Router Refactoring | Refactor 13 Category A `.get()` calls in `recommendations.py` to Pydantic models and dot-notation | M3 | ORIGINAL_REQUEST.md §R1, §R3 |
| 16 | Push Notifications & Referrals | Refactor 10 Category A `.get()` calls in `push_notifications.py` and `referrals.py` | M3 | ORIGINAL_REQUEST.md §R1-§R3 |
| 17 | Commission Router Refactoring | Refactor 9 Category A `.get()` calls in `commission.py` to pure dot-notation | M4 | ORIGINAL_REQUEST.md §R1, §R3 |
| 18 | Availability & Requests Refactoring | Refactor 8 Category A `.get()` calls in `availability_requests.py` and `seller_requests.py` | M4 | ORIGINAL_REQUEST.md §R1, §R3 |
| 19 | Financial & Support Refactoring | Refactor 10 Category A `.get()` calls in `payments.py` and `support_tickets.py` | M4 | ORIGINAL_REQUEST.md §R1, §R3 |
| 20 | Content & Metadata Refactoring | Refactor 11 Category A `.get()` calls in `content_pages.py`, `page_info.py`, `seller_availability.py`, `category_tags.py`, `feature_flags.py` | M4 | ORIGINAL_REQUEST.md §R1, §R3 |
| 21 | Clean Legacy Backup Files | Purge/clean `analytics.py.tmp` and `orders.py.bak` to prevent stale `.get` scanner false positives | M4 | Survey & R1 |
| 22 | Global Acceptance Verification | Verify zero Category A `.get(` across all 56 router files and app startup success | M5 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Core Foundation & Shared Schemas | `backend/app/models/schemas.py`, `backend/app/models/user.py` | None | PLANNED |
| M1 | Core E-Commerce & Ordering | `orders.py`, `products.py`, `returns.py`, `order_feedback.py` | M0 | PLANNED |
| M2 | Delivery & Logistics | `delivery_slots.py`, `delivery_charges.py`, `delivery_zones.py`, `valet_availability.py`, `valet_payout.py`, `tracking.py` | M0 | PLANNED |
| M3 | Identity, Analytics & User Interactions | `analytics.py`, `users.py`, `auth.py`, `recommendations.py`, `push_notifications.py`, `referrals.py` | M0 | PLANNED |
| M4 | Merchant, Financial & Content Operations | `commission.py`, `availability_requests.py`, `payments.py`, `page_info.py`, `support_tickets.py`, `content_pages.py`, `seller_availability.py`, `category_tags.py`, `feature_flags.py`, `seller_requests.py` | M0 | PLANNED |
| M5 | Global Acceptance & Test Verification | Full scan of `backend/app/routers/` + App Startup + Pytest run | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Pydantic Models ↔ Router Endpoints
- Any route accepting a JSON body must declare a Pydantic model parameter (e.g. `payload: MyPayloadModel`).
- Single-use, router-specific request bodies may be declared inline (`class MyPayload(BaseModel): ...`) in the router file.
- Shared models used across multiple routers or representing core entities must be placed in `backend/app/models/schemas.py`.
- Request models must define type hints and default values (`Optional[str] = None`, `int = 0`, etc.) matching their real-world schema.
- Access in route handlers must use direct dot notation (`payload.field`).
- Optional / nullable fields must be guarded using ternary fallbacks (`field if field is not None else default`).
- When passing data to the storage layer, convert models to dicts using `model.model_dump()` if the storage method expects a dictionary.
