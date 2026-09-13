# Handoff Report — Explorer 3 (Payload Schema Explorer)

## 1. Observation

### Observation 1.1: Endpoint Definitions with Raw/Generic Dict Parameters
Via AST scanning of all 55 router files in `backend/app/routers/` (479 total endpoints), exactly 4 endpoints directly accept raw `dict` / `Dict[str, Any]` or use `request.json()`:
1. `backend/app/routers/analytics.py:181-184`:
   ```python
   @router.post("/events", response_model=RecordEventResponse)
   async def record_event(
       event: Dict[str, Any] = Body(..., description="Analytics event payload"),
       user_info: Optional[dict] = Depends(get_optional_user),
   ):
   ```
   Lines 187–244 contain 21 calls to `.get()` on `event`, `enriched_event`, and `payload` (keys: `type`, `timestamp`, `sessionId`, `userId`, `page`, `returning`, `productId`, `productName`, `source`, `quantity`, `query`, `resultsCount`, `reason`).

2. `backend/app/routers/auth.py:184-200`:
   ```python
   @router.post("/msg91-webhook", response_model=Msg91WebhookResponse)
   async def msg91_webhook(request: Request, x_msg91_secret: Optional[str] = Header(None, alias="X-MSG91-Secret")):
       ...
       payload = await request.json()
       ...
       status_val = payload.get("Status") or payload.get("status") or payload.get("type")
   ```

3. `backend/app/routers/tracking.py:128-134`:
   ```python
   @router.post("/beacon", response_model=MessageResponse)
   @limiter.limit("60/minute")
   async def track_beacon(
       request: Request,
       payload: Dict[str, Any] = Body(default_factory=dict),
       current_user: Optional[dict] = Depends(get_optional_user),
   ):
   ```
   Line 140: Unpacks `**payload` directly into `tracking_repository.create({"type": "beacon", "userId": ..., **payload})`.

4. `backend/app/routers/tracking.py:457-460`:
   ```python
   @router.post("/notify-pincode", response_model=MessageResponse)
   async def track_notify_pincode(data: dict, current_user: Optional[dict] = Depends(get_optional_user)):
   ```
   Lines 460–467: Accesses `data.get("email")`, `data.get("productId")`, `data.get("productName")`, `data.get("pincode")`.

### Observation 1.2: Pydantic Request Models with Embedded Dict Fields
Three Pydantic request models across the routers contain raw `dict` / `Optional[dict]` / `List[dict]` fields:
1. `backend/app/routers/orders.py:112-129` (`OrderCreateRequest`):
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
   Lines 522–525, 752, 869, 1063–1066, 1492–1495 perform `.get()` on `order_data.shippingAddress` for `state`, `city`, `district`, `zipCode`, `pincode`.
   Lines 1486–1526 perform `.get()` on elements of `sellerDeliveryOptions` for `sellerId`, `deliverySlotId`, `deliverySlotDate`, `deliverySlotConfigId`.

2. `backend/app/routers/push_notifications.py:255-258` (`DeviceRegistrationRequest`):
   ```python
   class DeviceRegistrationRequest(BaseModel):
       userId: Optional[str] = None
       subscription: Optional[dict] = None
       expoToken: Optional[str] = None
   ```
   Line 303 performs `request.subscription.get("endpoint")`.

3. `backend/app/models/schemas.py:899-930` (`DeliveryChargeBase` / `DeliveryChargeUpdate`):
   ```python
   tiers: Optional[List[Dict]] = None
   ```

### Observation 1.3: Pydantic Model Accessed with Dictionary Workarounds
In `backend/app/routers/commission.py:244-266` (`update_commission_tiers`), `payload: TiersPayload` has `tiers: List[CommissionTier]`, where `CommissionTier` is already a strict Pydantic model (`id`, `minOrderValue`, `maxOrderValue`, `commissionPct`), but the handler accesses it with `.get()` and dict subscription:
```python
for t in payload.tiers:
    d = t
    if not d.get("id"):
        d["id"] = str(uuid4())
    tiers_data.append(d)
sorted_tiers = sorted(tiers_data, key=lambda t: t.minOrderValue)
for i in range(len(sorted_tiers) - 1):
    curr_max = sorted_tiers[i].get("maxOrderValue")
    next_min = sorted_tiers[i + 1]["minOrderValue"]
```

### Observation 1.4: Distribution of All 354 `.get()` Calls Across Routers
Running `scratch/categorize_gets.py` on all 55 router files identified 354 non-decorator `.get()` calls:
- 16 calls are on HTTP request headers (`request.headers.get(...)`) — exempt per R1.
- 26 calls are on in-memory caches or python dictionary lookups (e.g. `cache.get(...)`, `users_map.get(...)`).
- 85 calls are on request payloads, request models, or webhook dictionaries — primary targets for R1/R2/R3.
- 227 calls are on database documents, repository results, or internal data structures.

### Observation 1.5: FastAPI App Startup Verification
Running app import command in `backend/`:
```powershell
python -c "import sys; sys.path.insert(0, '.'); from app.main import app"
```
Produced:
```
TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'
```
Running `python -m pip check` produced:
```
fastapi 0.104.1 has requirement starlette<0.28.0,>=0.27.0, but you have starlette 1.6.0.
fastapi 0.104.1 has requirement anyio<4.0.0,>=3.7.1, but you have anyio 4.15.1.
```
Running router import verification across all 55 routers also revealed:
```
backend\app\models\user.py:1: ImportError: cannot import name 'CartItem' from 'app.models.schemas'
```
In `backend/app/models/user.py:1`, `CartItem`, `OrderItem`, and `VisibilityRule` are imported from `schemas.py` where they do not exist and are not used in `user.py`.

---

## 2. Logic Chain

1. From **Observation 1.1**, the 4 endpoints accepting raw dict/JSON request bodies (`analytics.py:181`, `auth.py:185`, `tracking.py:130`, `tracking.py:458`) cannot satisfy Requirement R1 ("zero results for request payloads") or R2 ("Introduce Pydantic Models") without defining explicit Pydantic request models.
2. From **Observation 1.2**, `OrderCreateRequest`, `DeviceRegistrationRequest`, and `DeliveryChargeBase` contain dict fields that directly force the router handlers in `orders.py` and `push_notifications.py` to use `.get()` to access `shippingAddress`, `sellerDeliveryOptions`, and `subscription`.
3. From checking `backend/app/models/schemas.py:731`, the existing schema `Address` already defines all address fields (`address`, `city`, `state`, `district`, `zipCode`, `country`, `googleLocation`, `latitude`, `longitude`), and can be directly reused for `shippingAddress` and `billingAddress` in `OrderCreateRequest`.
4. From **Observation 1.3**, `commission.py` demonstrates an anti-pattern where a Pydantic model (`CommissionTier`) was already in place, but legacy dictionary indexing (`d["id"]`) and `.get("maxOrderValue")` were used instead of dot notation (`t.id`, `t.maxOrderValue`).
5. From **Observation 1.4**, exactly 85 `.get()` calls belong to request payloads/models and must be replaced with Pydantic dot notation to satisfy Acceptance Criteria 1.
6. From **Observation 1.5**, app startup is blocked by an environment package mismatch (`starlette 1.6.0` vs required `0.27.0`) and an unused import error in `backend/app/models/user.py:1`. Aligning starlette to `0.27.0` and fixing `user.py:1` will restore app startup.

---

## 3. Caveats

1. **Client-side Telemetry Extensibility**: Both `analytics.py:181` (`/events`) and `tracking.py:130` (`/beacon`) receive client-side telemetry from web and mobile apps that may include arbitrary metadata. The replacement Pydantic models must use `model_config = ConfigDict(extra="allow")` so valid events with custom properties are not rejected with 422 Unprocessable Entity.
2. **Backward Compatibility for `zipCode` vs `pincode`**: In `orders.py:752`, `order_data.shippingAddress.get("zipCode") or order_data.shippingAddress.get("pincode")` was used. `Address` in `schemas.py:731` has `zipCode`. A computed property or field alias for `pincode` should be added to `Address` to prevent regression.
3. **Repository Dict Contracts**: In `push_notifications.py:321`, `push_notification_repository.registerDevice` expects a dict or `PushSubscription` object. Passing `request.subscription.model_dump()` maintains backward compatibility with storage.
4. **Environment Modifications**: As Explorer 3 is under strict read-only constraints, no source code or pip packages were modified during this survey.

---

## 4. Conclusion

1. **Scope of Payload Schemas Needed**:
   - **New Models Required**:
     - `AnalyticsEventPayload` and `AnalyticsEventCreate` (for `analytics.py:181`)
     - `Msg91WebhookPayload` (for `auth.py:185`)
     - `TrackBeaconRequest` (for `tracking.py:130`)
     - `TrackNotifyPincodeRequest` (for `tracking.py:458`)
     - `OrderItemCreate` and `SellerDeliveryOption` (for `orders.py:112`)
     - `PushSubscriptionKeys` and `PushSubscription` (for `push_notifications.py:255`)
     - `DeliveryChargeTier` (for `schemas.py:899`)
   - **Existing Models Reusable**:
     - `app.models.schemas.Address` for `OrderCreateRequest.shippingAddress` and `billingAddress`.
     - `app.models.schemas.CommissionTier` for `commission.py:update_commission_tiers`.
2. **Startup Restoration**:
   - Downgrade starlette: `pip install "starlette==0.27.0" "anyio==3.7.1"`
   - Fix `backend/app/models/user.py:1`: change import to `from app.models.schemas import AddressSnippet as Address, SellerPermissionSnippet as SellerPermissions`.

All detailed schemas, field mappings, before/after snippets, and categorization tables are recorded in `c:\Ecommerce app\.agents\explorer_survey_3\survey_report.md`.

---

## 5. Verification Method

### Step 1: Verify Payload Search
Run the following AST scanner from `c:\Ecommerce app\backend`:
```powershell
python scratch/find_all_dict_endpoints.py
```
Expected result prior to refactor: 4 endpoints found. After refactor: 0 endpoints found.

### Step 2: Verify .get() Elimination on Payloads
Run:
```powershell
python scratch/categorize_gets.py
```
Check that Category 3 ("Request payload/body .get() calls") drops to 0.

### Step 3: Verify FastAPI App Startup
After the environment alignment and import fix, run:
```powershell
python -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('SUCCESS:', app.title)"
```
Expected output: `SUCCESS: Stationery Junction API`.
