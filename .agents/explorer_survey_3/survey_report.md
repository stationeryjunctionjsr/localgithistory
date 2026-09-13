# Payload Schema Explorer Survey Report

**Explorer**: Explorer 3 (Payload Schema Explorer)  
**Date**: 2026-09-13  
**Working Directory**: `c:\Ecommerce app`  
**Target Scope**: `backend/app/routers/*.py`, `backend/app/models/schemas.py`, and FastAPI app startup  

---

## 1. Executive Summary

A systematic AST-based scan was performed across all 55 router files (`__init__.py` + 54 active endpoint router files) in `backend/app/routers/` encompassing **479 total endpoints**.

### Key Findings:
1. **Direct Dict/Untyped Request Body Endpoints (4 endpoints)**:
   - `analytics.py:181`: `POST /events` (`event: Dict[str, Any] = Body(...)`)
   - `auth.py:185`: `POST /msg91-webhook` (`request: Request` with `payload = await request.json()`)
   - `tracking.py:130`: `POST /beacon` (`payload: Dict[str, Any] = Body(default_factory=dict)`)
   - `tracking.py:458`: `POST /notify-pincode` (`data: dict`)

2. **Request Models with Embedded Dict Fields (3 models / endpoints)**:
   - `orders.py:112`: `OrderCreateRequest` (used in `POST /orders` at line 384) contains 4 dictionary fields:
     - `shippingAddress: dict`
     - `billingAddress: Optional[dict] = None`
     - `items: Optional[List[dict]] = None`
     - `sellerDeliveryOptions: Optional[List[dict]] = None`
   - `push_notifications.py:255`: `DeviceRegistrationRequest` (used in `POST /register-device` at line 297) contains:
     - `subscription: Optional[dict] = None`
   - `backend/app/models/schemas.py:899`: `DeliveryChargeBase` / `DeliveryChargeUpdate` (used in `delivery_charges.py`) contains:
     - `tiers: Optional[List[Dict]] = None`

3. **Pydantic Models Accessed with Dict Workarounds (1 endpoint)**:
   - `commission.py:244`: `PUT /tiers` (`payload: TiersPayload`) where `payload.tiers` contains `CommissionTier` (already a Pydantic model), but the endpoint logic accesses items with `.get("id")`, `d["id"]`, and `.get("maxOrderValue")`.

4. **All `.get()` Calls Across Routers (354 total non-decorator calls)**:
   - **Exempt (R1 standard usages)**: 16 request header calls (`request.headers.get(...)`).
   - **In-Memory Cache / Map Lookups**: 26 calls (e.g. `users_map.get(id)`, `cache.get(key)`).
   - **Request Payload / Body Attribute Lookups**: 85 calls (direct targets for replacement with strict model dot notation).
   - **Internal DB Docs / Domain Models Accessed via `.get()`**: 227 calls (models/dicts returned from repositories/storage).

5. **FastAPI App Startup Process**:
   - Python Environment: Python 3.14.2 (`C:\Python314\python.exe`).
   - Current Startup Status: **FAILS** due to two distinct pre-existing issues:
     a. Starlette 1.6.0 installed while FastAPI 0.104.1 requires `starlette<0.28.0,>=0.27.0` (as pinned in `requirements.txt:91`). Starlette 1.6.0 removed `on_startup` from `Router.__init__`.
     b. `backend/app/models/user.py:1` attempts `from app.models.schemas import Address, CartItem, OrderItem, VisibilityRule, SellerPermissions`, but `CartItem` does not exist in `schemas.py`.

---

## 2. Detailed Endpoint-by-Endpoint Analysis

### Endpoint 1: Analytics Event Ingestion (`analytics.py`)

- **Location**: `backend/app/routers/analytics.py:180-260`
- **Method & Route**: `POST /events`
- **Handler**: `async def record_event(event: Dict[str, Any] = Body(..., description="Analytics event payload"), user_info: Optional[dict] = Depends(get_optional_user))`
- **Current Problem**: Accepts raw `Dict[str, Any]` and extracts fields using 21 `.get()` calls across lines 187–244.

#### Fields Accessed from `event`:
| Field Name | Type Inferred | Required / Optional | Default Value | Usage Context |
|---|---|---|---|---|
| `type` | `str` | Required | None | Validated via `if not event.get("type"): raise HTTPException(400)` |
| `timestamp` | `Optional[str]` | Optional | `datetime.now(timezone.utc).isoformat()` | Event timestamp |
| `sessionId` | `Optional[str]` | Optional | `None` | User browsing session ID |
| `userId` | `Optional[str]` | Optional | `None` | Overridden with session user ID (`user_info.id`) |
| `page` | `Optional[str]` | Optional | `"/"` | Visited page for page_view events |
| `payload` | `Optional[Dict[str, Any]]` | Optional | `{}` | Nested event payload dictionary |

#### Fields Accessed from nested `payload`:
| Sub-field Name | Type Inferred | Required / Optional | Default Value | Usage Context |
|---|---|---|---|---|
| `returning` | `Optional[bool]` | Optional | `False` | `session_start` tracking |
| `productId` | `Optional[str]` | Optional | `None` | Product view, click, cart, wishlist |
| `productName` | `Optional[str]` | Optional | `"Unknown"` | Product view, click |
| `source` | `Optional[str]` | Optional | `"mobile_app"` | Product click source |
| `quantity` | `Optional[int]` | Optional | `1` | Cart add/remove quantity |
| `query` | `Optional[str]` | Optional | `""` | Search query text |
| `resultsCount` | `Optional[int]` | Optional | `0` | Search results count |
| `reason` | `Optional[str]` | Optional | `"unknown"` | `session_end` reason |

#### Schema Assessment:
- **Reuse existing in `schemas.py`?** No. No analytics event payload model currently exists.
- **New Pydantic Model Required**: Define `AnalyticsEventPayload` and `AnalyticsEventCreate` (or `RecordEventRequest`).
- Because mobile/web clients may pass arbitrary telemetry keys, models must use `model_config = ConfigDict(extra="allow")`.

#### Proposed Pydantic Schema:
```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any

class AnalyticsEventPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    returning: Optional[bool] = False
    productId: Optional[str] = None
    productName: Optional[str] = "Unknown"
    source: Optional[str] = "mobile_app"
    quantity: Optional[int] = 1
    query: Optional[str] = ""
    resultsCount: Optional[int] = 0
    reason: Optional[str] = "unknown"

class AnalyticsEventCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
    timestamp: Optional[str] = None
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    page: Optional[str] = "/"
    payload: Optional[AnalyticsEventPayload] = None
```

#### Proposed Handler Refactoring:
- Update signature to:
  `async def record_event(event: AnalyticsEventCreate, user_info: Optional[User] = Depends(get_optional_user)):`
- Replace `event.get("type")` with `event.type`
- Replace `event.get("timestamp")` with `event.timestamp or datetime.now(timezone.utc).isoformat()`
- Replace `user_info.get("_id")` with `user_info.id if user_info else None`
- Replace `event.get("payload")` with `payload = event.payload or AnalyticsEventPayload()`
- Access `payload.productId`, `payload.quantity`, `payload.query`, `payload.resultsCount`, `payload.reason` via dot notation.

---

### Endpoint 2: MSG91 Webhook (`auth.py`)

- **Location**: `backend/app/routers/auth.py:184-208`
- **Method & Route**: `POST /msg91-webhook`
- **Handler**: `async def msg91_webhook(request: Request, x_msg91_secret: Optional[str] = Header(None, alias="X-MSG91-Secret"))`
- **Current Problem**: Uses `payload = await request.json()` followed by `payload.get("Status") or payload.get("status") or payload.get("type")` and `payload.keys()`.

#### Fields Accessed from `payload`:
| Field Name | Type Inferred | Required / Optional | Default Value | Usage Context |
|---|---|---|---|---|
| `Status` / `status` | `Optional[str]` | Optional | `None` | Delivery status reported by MSG91 |
| `type` | `Optional[str]` | Optional | `None` | Event type fallback |
| (extra fields) | `Any` | Optional | `None` | Arbitrary webhook payload keys logged via `keys_summary` |

#### Schema Assessment:
- **Reuse existing in `schemas.py`?** No. `Msg91WebhookResponse` exists for the response, but no request model exists.
- **New Pydantic Model Required**: Define `Msg91WebhookPayload` with `ConfigDict(extra="allow")`.

#### Proposed Pydantic Schema:
```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class Msg91WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    status: Optional[str] = None
    Status: Optional[str] = None
    type: Optional[str] = None

    @property
    def effective_status(self) -> Optional[str]:
        return self.Status or self.status or self.type
```

#### Proposed Handler Refactoring:
- Update signature to:
  `async def msg91_webhook(payload: Msg91WebhookPayload, x_msg91_secret: Optional[str] = Header(None, alias="X-MSG91-Secret"))`
- Replace `status_val = payload.get("Status") ...` with `status_val = payload.effective_status`
- Replace `keys_summary = ",".join(sorted(payload.keys()))` with `keys_summary = ",".join(sorted(payload.model_dump().keys()))`

---

### Endpoint 3: Beacon Analytics Tracking (`tracking.py`)

- **Location**: `backend/app/routers/tracking.py:128-144`
- **Method & Route**: `POST /beacon`
- **Handler**: `async def track_beacon(request: Request, payload: Dict[str, Any] = Body(default_factory=dict), current_user: Optional[dict] = Depends(get_optional_user))`
- **Current Problem**: Accepts `payload: Dict[str, Any] = Body(default_factory=dict)` and un-types `current_user: Optional[dict]`.

#### Fields Accessed:
- Payload dictionary is unpacked directly via `**payload` into `tracking_repository.create({"type": "beacon", "userId": ..., **payload})`.

#### Schema Assessment:
- **Reuse existing in `schemas.py`?** No.
- **New Pydantic Model Required**: Define `TrackBeaconRequest` with `ConfigDict(extra="allow")`.

#### Proposed Pydantic Schema:
```python
class TrackBeaconRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    event: Optional[str] = None
    page: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None
```

#### Proposed Handler Refactoring:
- Update signature to:
  `async def track_beacon(request: Request, payload: TrackBeaconRequest = Body(default_factory=TrackBeaconRequest), current_user: Optional[User] = Depends(get_optional_user))`
- Replace `**payload` with `**payload.model_dump(exclude_unset=False)`.

---

### Endpoint 4: Notify Pincode Availability (`tracking.py`)

- **Location**: `backend/app/routers/tracking.py:457-474`
- **Method & Route**: `POST /notify-pincode`
- **Handler**: `async def track_notify_pincode(data: dict, current_user: Optional[dict] = Depends(get_optional_user))`
- **Current Problem**: `data: dict` parameter; accesses keys with `.get()` across lines 460–467.

#### Fields Accessed from `data`:
| Field Name | Type Inferred | Required / Optional | Default Value | Usage Context |
|---|---|---|---|---|
| `productId` | `str` | Required | `None` | Product ID requesting stock/service notification |
| `productName` | `Optional[str]` | Optional | `None` | Human-readable product name |
| `pincode` | `str` | Required | `None` | Customer delivery pincode |
| `email` | `Optional[str]` | Optional | `None` | Contact email if guest user |

#### Schema Assessment:
- **Reuse existing in `schemas.py`?** In `products.py:993`, `NotifyMeRequest` exists with only `email: Optional[str] = None` because `product_id` is a path parameter. For `POST /notify-pincode`, all fields are in the body.
- **New Pydantic Model Required**: Define `TrackNotifyPincodeRequest` in `app/models/schemas.py` or inline in `tracking.py`.

#### Proposed Pydantic Schema:
```python
class TrackNotifyPincodeRequest(BaseModel):
    productId: str
    pincode: str
    productName: Optional[str] = None
    email: Optional[str] = None
```

#### Proposed Handler Refactoring:
- Update signature to:
  `async def track_notify_pincode(data: TrackNotifyPincodeRequest, current_user: Optional[User] = Depends(get_optional_user)):`
- Replace:
  - `data.get("email")` -> `data.email`
  - `data.get("productId")` -> `data.productId`
  - `data.get("productName")` -> `data.productName`
  - `data.get("pincode")` -> `data.pincode`
  - `return {"success": True}` -> `return {"message": "Notification registered successfully"}` (matching `response_model=MessageResponse`)

---

## 3. Detailed Request Models with Embedded Dict Fields

### Model 1: `OrderCreateRequest` (`orders.py:112`)

- **Location**: `backend/app/routers/orders.py:112-130`
- **Current Definition**:
  ```python
  class OrderCreateRequest(BaseModel):
      shippingAddress: dict
      billingAddress: Optional[dict] = None
      paymentMethod: str = "cod"
      upiPaymentScreenshot: Optional[str] = None
      notes: Optional[str] = None
      couponCode: Optional[str] = None
      referralCode: Optional[str] = None
      discount: Optional[float] = 0
      printedBill: Optional[bool] = False
      items: Optional[List[dict]] = None
      isUrgentDelivery: Optional[bool] = False
      deliverySlotId: Optional[str] = None
      deliverySlotConfigId: Optional[str] = None
      deliverySlotDate: Optional[str] = None
      sellerDeliveryOptions: Optional[List[dict]] = None
  ```

#### Analysis of Embedded Dict Fields:
1. `shippingAddress: dict`:
   - Accessed in `orders.py`:
     - Line 522: `order_data.shippingAddress.get("state", "")`
     - Line 523: `order_data.shippingAddress.get("city", "")`
     - Line 524: `order_data.shippingAddress.get("district", "")`
     - Line 525: `order_data.shippingAddress.get("zipCode", "")`
     - Line 752: `order_data.shippingAddress.get("zipCode") or order_data.shippingAddress.get("pincode")`
     - Line 869: `order_data.shippingAddress.get("zipCode", "")`
     - Line 1063–1066: `state`, `city`, `district`, `zipCode`
     - Line 1492–1495: `state`, `city`, `district`, `zipCode`
   - **Schema Reuse**: `app.models.schemas.Address` (line 731) matches this structure completely:
     `address`, `city`, `state`, `district`, `zipCode`, `country`, `googleLocation`, `latitude`, `longitude`.
   - **Action**: Change `shippingAddress: Address` and `billingAddress: Optional[Address] = None`. Add property/alias `pincode` -> `zipCode` if needed.

2. `items: Optional[List[dict]] = None`:
   - Accessed in `orders.py` lines 496–517, 630–651:
     - `item.product or item.product_id`
     - `item.quantity`
     - `item.sell_as_case` / `item.sellAsCase`
     - `item.selectedVariation`
   - **Action**: Define `OrderItemCreate`:
     ```python
     class OrderItemCreate(BaseModel):
         productId: Optional[str] = Field(None, alias="product_id")
         product: Optional[str] = None
         quantity: int = 1
         sellAsCase: Optional[bool] = Field(False, alias="sell_as_case")
         selectedVariation: Optional[VariantOption] = None
     ```

3. `sellerDeliveryOptions: Optional[List[dict]] = None`:
   - Accessed in `orders.py` lines 1486–1526:
     - `sdo.get("sellerId")`
     - `sdo.get("deliverySlotId")`
     - `sdo.get("deliverySlotDate")`
     - `sdo.get("deliverySlotConfigId")`
     - `sdo.get("isUrgentDelivery")`
   - **Action**: Define `SellerDeliveryOption`:
     ```python
     class SellerDeliveryOption(BaseModel):
         sellerId: str
         deliverySlotId: Optional[str] = None
         deliverySlotDate: Optional[str] = None
         deliverySlotConfigId: Optional[str] = None
         isUrgentDelivery: Optional[bool] = False
     ```

---

### Model 2: `DeviceRegistrationRequest` (`push_notifications.py:255`)

- **Location**: `backend/app/routers/push_notifications.py:255-259`
- **Current Definition**:
  ```python
  class DeviceRegistrationRequest(BaseModel):
      userId: Optional[str] = None
      subscription: Optional[dict] = None
      expoToken: Optional[str] = None
  ```
- **Field Accessed**:
  - Line 303: `has_web_subscription = request.subscription and request.subscription.get("endpoint")`
  - In repository `push_notification_repository.py:109-121`:
    - `subscription.get("endpoint")`
    - `subscription.get("keys", {})`
- **Proposed Pydantic Schema**:
  ```python
  class PushSubscriptionKeys(BaseModel):
      p256dh: str
      auth: str

  class PushSubscription(BaseModel):
      endpoint: str
      expirationTime: Optional[float] = None
      keys: PushSubscriptionKeys

  class DeviceRegistrationRequest(BaseModel):
      userId: Optional[str] = None
      subscription: Optional[PushSubscription] = None
      expoToken: Optional[str] = None
  ```

---

### Model 3: `DeliveryChargeBase` / `DeliveryChargeUpdate` (`schemas.py:899` & `delivery_charges.py`)

- **Location**: `backend/app/models/schemas.py:899-940`
- **Current Field**: `tiers: Optional[List[Dict]] = None`
- **Fields Accessed in `delivery_charge_repository.py:69-72, 279-292`**:
  - `minAmount: Optional[float] = 0.0`
  - `maxAmount: Union[float, str]`
  - `charge: float`
- **Proposed Pydantic Schema**:
  ```python
  class DeliveryChargeTier(BaseModel):
      minAmount: Optional[float] = 0.0
      maxAmount: Union[float, str]
      charge: float

  # Updated DeliveryChargeBase / DeliveryChargeUpdate:
  # tiers: Optional[List[DeliveryChargeTier]] = None
  ```

---

### Model 4: `TiersPayload` (`commission.py:105`)

- **Location**: `backend/app/routers/commission.py:105-108, 244-282`
- **Current Definition**:
  ```python
  class CommissionTier(BaseModel):
      id: Optional[str] = Field(default=None)
      minOrderValue: float = Field(..., ge=0)
      maxOrderValue: Optional[float] = Field(default=None, ge=0)
      commissionPct: float = Field(..., ge=0, le=100)

  class TiersPayload(BaseModel):
      tiers: List[CommissionTier]
      defaultCommissionPct: float = Field(default=5.0, ge=0, le=100)
  ```
- **Current Workaround in Handler (lines 251–262)**:
  ```python
  for t in payload.tiers:
      d = t
      if not d.get("id"):     # Calling .get() on Pydantic model!
          d["id"] = str(uuid4()) # Subscripting Pydantic model!
  ...
  curr_max = sorted_tiers[i].get("maxOrderValue") # Calling .get() on model!
  next_min = sorted_tiers[i + 1]["minOrderValue"] # Subscripting model!
  ```
- **Fix**: Update handler to use `t.id = str(uuid4())`, `sorted_tiers[i].maxOrderValue`, and `sorted_tiers[i + 1].minOrderValue`.

---

## 4. Categorization of All 354 `.get()` Calls in Routers

| Category | Count | Sample Locations | Action Required |
|---|---|---|---|
| **Request Headers (Exempt per R1)** | 16 | `activity.py:17`, `activity.py:51` (`request.headers.get(...)`) | Exempt. Keep as-is. |
| **In-Memory Cache / Map Lookups** | 26 | `recommendations.py:122` (`cache.get(key)`), `users.py:168` (`avail_map.get(vid)`), `orders.py:224` (`users_map.get(uid)`) | Valid Python dictionary lookups on maps/caches. Keep as-is. |
| **Request Payload / Body Attribute Lookups** | 85 | `analytics.py:187-244` (`event.get`, `payload.get`), `orders.py:522-1526` (`order_data.shippingAddress.get`, `sdo.get`), `tracking.py:460-467` (`data.get`), `auth.py:200` (`payload.get`) | **Must be eliminated**: replace with strict Pydantic dot notation (`payload.field`). |
| **Internal DB Docs / Domain Models** | 227 | `orders.py:47` (`sellers[0].get("id")`), `delivery_slots.py:141` (`config.get("slots")`), `products.py:112` (`main_row.get(...)`), `returns.py:168` (`shipping_address.get(...)`), `commission.py:253` (`t.get("id")`) | Replace with dot notation on domain models / Pydantic schemas (`seller.id`, `config.slots`, etc.). |

---

## 5. FastAPI App Startup Process & Environment Verification

### Environment Specification
- **Python Executable**: `C:\Python314\python.exe`
- **Python Version**: `3.14.2`
- **Operating System**: Windows 11 / Windows Server (win32)
- **Primary Package Versions**:
  - `fastapi`: `0.104.1`
  - `pydantic`: `2.12.5`
  - `pydantic-core`: `2.41.5`
  - `pydantic-settings`: `2.12.0`
  - `starlette`: `1.6.0` (mismatched; `requirements.txt` specifies `0.27.0`)
  - `anyio`: `4.15.1` (mismatched; `fastapi 0.104.1` requires `<4.0.0,>=3.7.1`)

### Verification Command
To verify whether the FastAPI application imports and starts cleanly:
```powershell
python -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('App successfully loaded:', app.title)"
```
Or to run the Uvicorn server directly:
```powershell
python run.py
```

### Current Startup Result: FAILS
The app currently encounters two fatal errors during import:

#### Error 1: Starlette 1.6.0 Incompatibility
- **Command Output**:
  ```
  TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'
  ```
- **Root Cause**:
  `pip check` reports:
  ```
  fastapi 0.104.1 has requirement starlette<0.28.0,>=0.27.0, but you have starlette 1.6.0.
  fastapi 0.104.1 has requirement anyio<4.0.0,>=3.7.1, but you have anyio 4.15.1.
  ```
  In Starlette 1.6.0, `Router.__init__` removed `on_startup`. However, `fastapi 0.104.1` instantiates `routing.APIRouter` passing `on_startup=on_startup` to `super().__init__`.
- **Resolution for Implementer**:
  Install the exact version pinned in `backend/requirements.txt`:
  ```powershell
  pip install "starlette==0.27.0" "anyio==3.7.1"
  ```

#### Error 2: Broken Imports in `backend/app/models/user.py`
- **Command Output**:
  ```
  ImportError: cannot import name 'CartItem' from 'app.models.schemas' (C:\Ecommerce app\backend\app\models\schemas.py)
  ```
- **Root Cause**:
  In `backend/app/models/user.py` line 1:
  ```python
  from app.models.schemas import Address, CartItem, OrderItem, VisibilityRule, SellerPermissions
  ```
  In `backend/app/models/schemas.py`, there is no `CartItem`, `OrderItem`, `VisibilityRule`, or `SellerPermissions`. (Compare `sub_order.py:1` which correctly aliased `AddressSnippet as Address, ItemSnippet as CartItem, ItemSnippet as OrderItem, SellerPermissionSnippet as SellerPermissions`). Moreover, in `user.py`, `CartItem`, `OrderItem`, and `VisibilityRule` are not even used.
- **Resolution for Implementer**:
  Update `backend/app/models/user.py:1` to:
  ```python
  from app.models.schemas import AddressSnippet as Address, SellerPermissionSnippet as SellerPermissions
  ```

---

## 6. Implementation Action Plan for Downstream Agents

1. **Step 1: Environment Alignment**
   Run:
   ```powershell
   pip install "starlette==0.27.0" "anyio==3.7.1"
   ```
   Fix line 1 of `backend/app/models/user.py` to resolve the `CartItem` import failure.

2. **Step 2: Add Required Pydantic Schemas to `backend/app/models/schemas.py`**
   - `AnalyticsEventPayload` and `AnalyticsEventCreate`
   - `Msg91WebhookPayload`
   - `TrackBeaconRequest`
   - `TrackNotifyPincodeRequest`
   - `SellerDeliveryOption`
   - `OrderItemCreate`
   - `PushSubscriptionKeys` and `PushSubscription`
   - `DeliveryChargeTier`

3. **Step 3: Update Routers with Strict Dot Notation**
   - `backend/app/routers/analytics.py`: Replace `event: Dict[str, Any]` with `AnalyticsEventCreate` and replace `.get()` calls with dot notation.
   - `backend/app/routers/auth.py`: Replace `payload = await request.json()` with `payload: Msg91WebhookPayload` and use `payload.effective_status`.
   - `backend/app/routers/tracking.py`: Replace `payload: Dict[str, Any]` with `TrackBeaconRequest` and `data: dict` with `TrackNotifyPincodeRequest`.
   - `backend/app/routers/orders.py`: Update `OrderCreateRequest` to type `shippingAddress: Address`, `billingAddress: Optional[Address]`, `items: Optional[List[OrderItemCreate]]`, `sellerDeliveryOptions: Optional[List[SellerDeliveryOption]]`. Replace all `.get()` accessors with dot notation.
   - `backend/app/routers/push_notifications.py`: Update `DeviceRegistrationRequest` to type `subscription: Optional[PushSubscription]`. Replace `.get("endpoint")` with `.endpoint`.
   - `backend/app/routers/commission.py`: Replace `.get("id")`, `d["id"]`, `.get("maxOrderValue")` with dot notation on `CommissionTier`.

4. **Step 4: Verification**
   - Run `python -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('Startup successful')"`
   - Search for `.get(` across `backend/app/routers/` to verify zero payload/internal dictionary workarounds remain.
