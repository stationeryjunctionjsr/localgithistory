# Dispatch — Worker M0 (worker_m0_2)

## 2026-09-13T18:19:30+05:30

### Working Directory
`c:\Ecommerce app\.agents\worker_m0_2`

### Objective
Implement Milestone M0: Core Foundation & Shared Schemas in `backend/app/models/schemas.py` and `backend/app/models/user.py` so that `app.main` imports cleanly and all common request/response DTOs are ready for downstream router refactoring.

### Mandatory Documents to Read First
- `c:\Ecommerce app\.agents\ORIGINAL_REQUEST.md`
- `c:\Ecommerce app\PROJECT.md`
- `c:\Ecommerce app\.agents\explorer_survey_1\survey_report.md`
- `c:\Ecommerce app\.agents\explorer_survey_3\survey_report.md`

### Scope & Specific Instructions
1. In `backend/app/models/schemas.py`:
   - Add `AdSummaryResponse` (referenced in `backend/app/routers/ads.py:3`).
   - Add aliases / exports for snippets:
     ```python
     CartItem = ItemSnippet
     OrderItem = ItemSnippet
     VisibilityRule = VisibilityRuleSnippet
     SellerPermissions = SellerPermissionSnippet
     Address = AddressSnippet  # if not already present
     ```
   - Add common payload schemas needed across routers (per Survey 3):
     - `AnalyticsEventPayload` and `AnalyticsEventCreate` (with `model_config = ConfigDict(extra="allow")`)
     - `Msg91WebhookPayload` (with `model_config = ConfigDict(extra="allow", populate_by_name=True)`)
     - `TrackBeaconRequest` (with `model_config = ConfigDict(extra="allow")`)
     - `TrackNotifyPincodeRequest`
     - `SellerDeliveryOption`
     - `OrderItemCreate`
     - `PushSubscriptionKeys` and `PushSubscription`
     - `DeliveryChargeTier`
   - Add missing response models identified in Survey 1 §5.3 if any routers fail to import:
     `ActivityLogResponse`, `AvailabilityRequestResponse`, `DeliveryZoneResponse`, `EligibleFeedbackResponse`, `ReturnEligibilityResponse`, `SupportTicketResponse`, `UPIDetailsResponse`, `ValetPayoutSettingsResponse`.
2. In `backend/app/models/user.py`:
   - Fix imports so line 1 does not fail on missing names (e.g. `from app.models.schemas import AddressSnippet as Address, SellerPermissionSnippet as SellerPermissions`).
3. Verification:
   - Run from `backend/`: `python -c "import app.main; print('App Main Import Succeeded!')"`
   - Run from `backend/`: `python -m pytest tests/test_health.py`
   - If any other router has a simple syntax or missing import preventing `app.main` from loading, fix it so `import app.main` succeeds!

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Deliverables
Write your comprehensive `handoff.md` and `progress.md` in `c:\Ecommerce app\.agents\worker_m0_2\`. Send a completion message back to orchestrator_2.
