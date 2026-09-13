# Test Infrastructure & Validation Architecture

## Overview
This document specifies the testing architecture, validation methodology, and progressive verification framework for eliminating dictionary workarounds (`.get(`) across all 55 active router modules in `backend/app/routers/` and enforcing strict Pydantic models per the gold standard established in `backend/app/routers/ads.py`.

The test suite is implemented in:
```
backend/tests/test_router_pydantic_refactor.py
```

---

## 1. 4-Tier Test Architecture

The verification suite employs a multi-tiered defense-in-depth strategy combining static AST analysis, application startup integrity verification, route signature contract enforcement, and runtime schema validation with HTTP 422 error simulation.

```
+-------------------------------------------------------------------------------+
| Tier 1: Static AST Analysis                                                   |
| - Parse all 55 active routers in backend/app/routers/*.py                     |
| - Verify ZERO Category A .get( dictionary workarounds                         |
| - Rigorous exemption filtering (headers, query params, decorators, DB repos)  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Tier 2: Application Startup & Route Registration Check                        |
| - Import app.main.app without syntax, import, or Pydantic definition errors   |
| - Verify FastAPI instance validity and non-empty route table                  |
| - Verify all expected router prefixes are registered                          |
| - Generate OpenAPI specification schema without schema generation exceptions  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Tier 3: Endpoint Signature & Type Hint Check                                  |
| - Inspect all route handler functions across all active routers               |
| - Assert no route endpoint accepts raw `payload: dict` or `data: dict`        |
| - Ensure request bodies are declared as strict Pydantic BaseModel subclasses  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Tier 4: Schema Validation & HTTP 422 Error Rejection                          |
| - Test Pydantic models reject invalid inputs with ValidationError / HTTP 422  |
| - Test valid payloads parse successfully into dot-notation accessible objects |
| - Test optional fields and ternary fallback defaults                          |
| - Test .model_dump() serialization for persistence layer handoff              |
+-------------------------------------------------------------------------------+
```

---

## 2. Tier Specifications

### Tier 1: Static AST Analysis (Zero Category A `.get(` Calls)
- **Objective**: Statically inspect every active Python router file in `backend/app/routers/` to ensure zero dictionary `.get(` workarounds exist on request payloads, models, or internal dictionaries.
- **Mechanism**: `ast.parse()` extracts the full Abstract Syntax Tree of each file. An `ast.NodeVisitor` identifies every `ast.Call` where `func` is an attribute access with `attr == 'get'`.
- **Granularity**: Parameterized per router file (`test_tier1_router_ast_zero_get[<router_file>]`), plus aggregate repository-level assertions (`test_tier1_all_routers_aggregate_zero_disallowed_get`).
- **Exemption Matrix**:
  | Call Pattern | Classification | Rationale |
  |---|---|---|
  | `@router.get(...)` / `@app.get(...)` | Category B (Exempt) | FastAPI HTTP GET route registration decorator |
  | `request.headers.get(...)` | Category B (Exempt) | Standard HTTP request header lookup |
  | `request.query_params.get(...)` | Category B (Exempt) | Standard HTTP request query parameter lookup |
  | `request.cookies.get(...)` | Category B (Exempt) | Standard HTTP request cookie lookup |
  | `*_repository.get(...)` / `repo.get(...)` | Category B (Exempt) | Database repository singleton fetch method |
  | In-memory lookup maps (`*_map.get(...)`) | Category B (Exempt) | Dynamic bulk join hash tables (e.g. `product_map`, `users_map`) |
  | In-memory caches (`cache.get`, `_guest_rec_cache.get`) | Category B (Exempt) | Cache retrieval mechanism |
  | Frequency counters (`returned_items_qty.get`) | Category B (Exempt) | Accumulator pattern dictionary |
  | Platform config (`min_versions.get`) | Category B (Exempt) | Static OS/platform mapping table |
  | `payload.get(...)`, `data.get(...)`, `order.get(...)` | Category A (Disallowed) | Dictionary workaround on payload/entity; MUST be refactored |

### Tier 2: Application Startup & Route Registration Check
- **Objective**: Guarantee that the FastAPI application initializes without import cycles, syntax errors, or invalid Pydantic schema declarations.
- **Tests**:
  1. `test_tier2_app_startup_and_valid_fastapi_instance`: Imports `app.main.app` and asserts `isinstance(app, FastAPI)` and `len(app.routes) > 0`.
  2. `test_tier2_all_expected_router_prefixes_registered`: Confirms that all core routers (`/api/ads`, `/api/orders`, `/api/products`, `/api/auth`, `/api/analytics`, `/api/delivery-slots`, `/api/returns`, `/api/commission`, `/api/tracking`, `/api/users`, etc.) are mounted in the FastAPI route table.
  3. `test_tier2_openapi_schema_generation`: Invokes `app.openapi()` to generate the full OpenAPI 3.0 schema and asserts that `"openapi"`, `"info"`, and `"paths"` exist and render without Pydantic schema generation failures.

### Tier 3: Route Endpoint Signature Check
- **Objective**: Guarantee that no route handler endpoint accepts raw untyped dictionaries (`dict`, `Dict`, `Dict[str, Any]`) as request body payloads.
- **Mechanism**: Statically inspects the AST of all functions decorated with `@router.<method>` (`post`, `put`, `patch`, `delete`, `get`, `api_route`).
- **Assertion**: Parameters representing request bodies (not annotated with `Depends(...)`) must NOT be annotated with `dict`, `Dict`, `Dict[str, Any]`, `dict[str, Any]`, or `Any`.
- **Granularity**: Parameterized per router file (`test_tier3_router_signatures_no_raw_dict[<router_file>]`), plus aggregate assertions (`test_tier3_all_routers_aggregate_signatures`).

### Tier 4: Schema Validation & HTTP 422 Error Rejection
- **Objective**: Verify that Pydantic models enforce schema contracts: rejecting invalid payloads with HTTP 422 Unprocessable Entity / `ValidationError` and accepting valid payloads via direct dot-notation access.
- **Coverage**:
  - **Ads Domain (`ads.py`)**: `AdCreate`, `AdUpdate`, `AdStatusUpdate`, `AdEventPayload`, `AdStats`, `AdSummaryResponse`.
  - **Analytics Domain (`analytics.py`)**: `AnalyticsEventCreate` / `AnalyticsEventPayload`.
  - **Tracking Domain (`tracking.py`)**: `NotifyPincodePayload`, `TrackingBeacon`.
  - **Auth Domain (`auth.py`)**: `Msg91WebhookPayload`, `RefreshTokenRequest`, `SendOtpRequest`.
  - **Delivery & Slots Domain (`delivery_slots.py`)**: `DeliverySlot`, `DeliverySlotConfigCreate`.
  - **Orders Domain (`orders.py`)**: `ShippingAddress`, `OrderItemCreate`, `CreateOrderRequest`.
  - **Commission Domain (`commission.py`)**: `CommissionTier`, `CommissionUpdateRequest`.
  - **Returns Domain (`returns.py`)**: `ReturnRequestCreate`.
  - **Opaque-Box HTTP Testing**: ASGI test client verifies that malformed requests return HTTP 422 with structured `"detail"` indicating field errors.

---

## 3. Test Execution Guide

### Primary Test Command
To run the refactoring test suite from the repository root:
```bash
python -m pytest backend/tests/test_router_pydantic_refactor.py
```

### Pre-M0 Test Execution (Conftest Bypass)
Before Milestone M0 (Core Schema Unblocking) is completed, `backend/tests/conftest.py` cannot import `app.main` due to missing schema imports (`CartItem`, `ActivityLogResponse`). To run tests during this phase:
```bash
python -m pytest --noconftest backend/tests/test_router_pydantic_refactor.py
```

### Running Specific Tiers
- **Tier 1 (AST Analysis)**:
  ```bash
  python -m pytest --noconftest backend/tests/test_router_pydantic_refactor.py -k "tier1"
  ```
- **Tier 2 (App Startup)**:
  ```bash
  python -m pytest --noconftest backend/tests/test_router_pydantic_refactor.py -k "tier2"
  ```
- **Tier 3 (Signatures)**:
  ```bash
  python -m pytest --noconftest backend/tests/test_router_pydantic_refactor.py -k "tier3"
  ```
- **Tier 4 (Validation & 422)**:
  ```bash
  python -m pytest --noconftest backend/tests/test_router_pydantic_refactor.py -k "tier4"
  ```

---

## 4. Progressive Testability & Milestone Integration

The test suite is designed for progressive verification as implementation milestones progress:

| Milestone | Target Scope | Initial Status | Target Status |
|---|---|:---:|:---:|
| **Baseline** | Initial Codebase (Pre-M0) | 29 Tier 1 PASS, 26 Tier 1 FAIL | Baseline established |
| **M0** | `schemas.py`, `user.py`, `activity.py` | Tier 2 Fails (ImportError) | Tier 2 PASS |
| **M1** | `orders.py`, `products.py`, `returns.py`, `order_feedback.py` | Tier 1 & 3 Fail on M1 files | Tier 1 & 3 PASS on M1 files |
| **M2** | `delivery_slots.py`, `delivery_charges.py`, `delivery_zones.py`, `valet_*.py`, `tracking.py` | Tier 1 & 3 Fail on M2 files | Tier 1 & 3 PASS on M2 files |
| **M3** | `analytics.py`, `users.py`, `auth.py`, `recommendations.py`, `push_notifications.py`, `referrals.py` | Tier 1 & 3 Fail on M3 files | Tier 1 & 3 PASS on M3 files |
| **M4** | `commission.py`, `availability_requests.py`, `payments.py`, `page_info.py`, content routers | Tier 1 & 3 Fail on M4 files | Tier 1 & 3 PASS on M4 files |
| **M5** | Full Repository Scan | Partial | 100% PASS Across All 4 Tiers |

---

## 5. Test Integrity & Audit Safeguards

1. **Zero Facades**: Tests execute real AST parsing of router source code and real Pydantic validation logic.
2. **Deterministic & Self-Contained**: Tests do not require external databases, network connections, or stateful mutation.
3. **Transparent Failure Reporting**: When a Tier 1 or Tier 3 test fails, the error message outputs the exact file, line number, caller expression, arguments, and source line for immediate developer remediation.
