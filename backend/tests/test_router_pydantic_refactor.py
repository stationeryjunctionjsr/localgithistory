"""Opaque-Box E2E & Static Test Suite for Router Pydantic Refactoring.

Comprehensive 4-Tier verification suite:
- Tier 1: Static AST verification across all backend/app/routers/*.py asserting ZERO
          Category A dictionary .get( workarounds on request payloads/internal models.
- Tier 2: FastAPI application startup, router prefix registration, and OpenAPI schema generation.
- Tier 3: Endpoint signature check ensuring no route handler accepts raw payload: dict or data: dict.
- Tier 4: Pydantic schema validation contracts, dot-notation access, and HTTP 422 rejection.

Authoritative Reference:
- Pattern established in backend/app/routers/ads.py
- Requirements R1-R3 in .agents/ORIGINAL_REQUEST.md
- Implementation plan in PROJECT.md
"""

import ast
import glob
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest
from fastapi import APIRouter, FastAPI, status
from pydantic import BaseModel, Field, ValidationError
from starlette.testclient import TestClient

# Ensure backend root is on sys.path regardless of execution CWD
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

ROUTERS_DIR = os.path.join(BACKEND_DIR, "app", "routers")

# Discover all active router python files (excluding backup/temporary legacy files)
ALL_ROUTER_PATHS = sorted(glob.glob(os.path.join(ROUTERS_DIR, "*.py")))
ACTIVE_ROUTER_FILES = [os.path.basename(p) for p in ALL_ROUTER_PATHS]

# Known exempt callers for Category B AST filtering per survey report & specifications
EXEMPT_CALLERS: Set[str] = {
    "router",
    "app",
    # Dynamic in-memory lookup maps & caches (Category B in survey_report.md)
    "product_map",
    "products_map",
    "users_map",
    "payments_map",
    "order_map",
    "valets_map",
    "sellers_map",
    "seller_docs",
    "seller_delivery_map",
    "avail_map",
    "cache",
    "_guest_rec_cache",
    "_cart_products_map",
    "returned_items_qty",
    "min_versions",
}

ROUTE_DECORATOR_METHODS: Set[str] = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "api_route",
}


# ==============================================================================
# Helper Classes & AST Analyzers
# ==============================================================================


class CategoryAGetVisitor(ast.NodeVisitor):
    """AST visitor to detect Category A dictionary .get( workarounds.

    Category A: Disallowed .get( calls on request payloads, DB documents, or internal entities.
    Category B: Allowed exemptions (headers, query_params, cookies, decorators, DB repos, caches).
    """

    def __init__(self, filename: str, source_lines: List[str]):
        self.filename = filename
        self.source_lines = source_lines
        self.violations: List[Tuple[int, str, str, str]] = []
        self.exemptions: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            caller_str = ast.unparse(node.func.value)
            args_str = ", ".join(ast.unparse(a) for a in node.args)

            # Exemption 1: Direct exempt callers (router, app, in-memory caches / lookup maps)
            if caller_str in EXEMPT_CALLERS:
                self.exemptions.append((node.lineno, caller_str))
            # Exemption 2: HTTP Request standard properties (request.headers, request.query_params, request.cookies)
            elif (
                caller_str.endswith(".headers")
                or caller_str.endswith(".query_params")
                or caller_str.endswith(".cookies")
            ):
                self.exemptions.append((node.lineno, caller_str))
            # Exemption 3: Database repository singleton fetch methods (repo.get(), *_repository.get())
            elif caller_str.endswith("_repository") or caller_str == "repository":
                self.exemptions.append((node.lineno, caller_str))
            else:
                line_text = (
                    self.source_lines[node.lineno - 1].strip() if 0 <= node.lineno - 1 < len(self.source_lines) else ""
                )
                self.violations.append((node.lineno, caller_str, args_str, line_text))

        self.generic_visit(node)


class RouteSignatureVisitor(ast.NodeVisitor):
    """AST visitor to detect route handlers accepting raw dict payloads."""

    def __init__(self, filename: str, source_lines: List[str]):
        self.filename = filename
        self.source_lines = source_lines
        self.violations: List[Tuple[int, str, str, str, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_route_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_route_function(node)
        self.generic_visit(node)

    def _check_route_function(self, node):
        is_route_endpoint = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ROUTE_DECORATOR_METHODS:
                    is_route_endpoint = True
                    break

        if not is_route_endpoint:
            return

        for arg in node.args.args:
            arg_name = arg.arg
            num_defaults = len(node.args.defaults)
            pos = node.args.args.index(arg)
            default_idx = pos - (len(node.args.args) - num_defaults)
            default_str = ""
            if default_idx >= 0:
                default_str = ast.unparse(node.args.defaults[default_idx])

            # Injected dependencies (e.g. Depends(get_current_user)) are not request body payloads
            if "Depends" in default_str:
                continue

            ann_str = ast.unparse(arg.annotation) if arg.annotation else ""
            ann_lower = ann_str.lower()

            is_raw_dict = (
                "dict" in ann_lower
                or ann_lower in ("any", "typing.any")
                or (arg_name in ("payload", "data", "body") and not ann_str)
            )

            if is_raw_dict:
                line_text = (
                    self.source_lines[node.lineno - 1].strip() if 0 <= node.lineno - 1 < len(self.source_lines) else ""
                )
                self.violations.append((node.lineno, node.name, arg_name, ann_str, line_text))


def get_ast_violations_for_file(filepath: str) -> List[Tuple[int, str, str, str]]:
    """Parse a router file and return all Category A .get( violations."""
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=filepath)
    visitor = CategoryAGetVisitor(os.path.basename(filepath), lines)
    visitor.visit(tree)
    return visitor.violations


def get_signature_violations_for_file(filepath: str) -> List[Tuple[int, str, str, str, str]]:
    """Parse a router file and return all route handlers taking raw dict payloads."""
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=filepath)
    visitor = RouteSignatureVisitor(os.path.basename(filepath), lines)
    visitor.visit(tree)
    return visitor.violations


# ==============================================================================
# TIER 1: Static AST Analysis (Zero Category A .get( Calls)
# ==============================================================================


class TestTier1ASTStaticAnalysis:
    """Tier 1: AST / Static check verifying zero Category A .get( calls across routers."""

    def test_tier1_router_inventory_complete(self):
        """Assert that all 55 active router files are discovered and tested."""
        assert len(ACTIVE_ROUTER_FILES) == 55, (
            f"Expected exactly 55 active router files, found {len(ACTIVE_ROUTER_FILES)}: {ACTIVE_ROUTER_FILES}"
        )

    def test_tier1_reference_router_ads_clean(self):
        """Verify the gold standard reference router (ads.py) contains ZERO Category A calls."""
        ads_path = os.path.join(ROUTERS_DIR, "ads.py")
        violations = get_ast_violations_for_file(ads_path)
        assert len(violations) == 0, f"Gold standard ads.py has unexpected violations: {violations}"

    @pytest.mark.parametrize("router_filename", ACTIVE_ROUTER_FILES)
    def test_tier1_router_ast_zero_get(self, router_filename: str):
        """Verify that individual router module has zero Category A .get( dictionary workarounds."""
        filepath = os.path.join(ROUTERS_DIR, router_filename)
        violations = get_ast_violations_for_file(filepath)

        if violations:
            formatted_violations = "\n".join(
                f"  - L{lineno}: {caller}.get({args}) -> '{line}'" for lineno, caller, args, line in violations
            )
            pytest.fail(
                f"Router '{router_filename}' contains {len(violations)} Category A dictionary workaround(s):\n"
                f"{formatted_violations}\n"
                f"Refactor to Pydantic models with direct dot-notation access per ads.py."
            )

    def test_tier1_all_routers_aggregate_zero_disallowed_get(self):
        """Aggregate assertion verifying zero Category A .get( calls across the entire repository."""
        all_violations: Dict[str, List[Tuple[int, str, str, str]]] = {}
        total_violations_count = 0

        for router_file in ACTIVE_ROUTER_FILES:
            filepath = os.path.join(ROUTERS_DIR, router_file)
            violations = get_ast_violations_for_file(filepath)
            if violations:
                all_violations[router_file] = violations
                total_violations_count += len(violations)

        if total_violations_count > 0:
            summary_lines = [
                f"Found {total_violations_count} total Category A .get( calls across {len(all_violations)} files:"
            ]
            for r_file, viols in sorted(all_violations.items()):
                summary_lines.append(f"  - {r_file}: {len(viols)} violation(s)")
            pytest.fail("\n".join(summary_lines))


# ==============================================================================
# TIER 2: Application Startup & Route Registration Check
# ==============================================================================


class TestTier2AppStartupAndRoutes:
    """Tier 2: App Startup check: import app.main and verify app is a valid FastAPI instance."""

    def test_tier2_app_startup_and_valid_fastapi_instance(self):
        """Import app.main and verify app is a valid FastAPI instance with registered routes."""
        try:
            from app.main import app
        except Exception as exc:
            pytest.fail(
                f"FastAPI application failed to start up or import app.main: {exc}\n"
                f"Ensure Milestone M0 (Core Schema Unblocking) has restored schema imports."
            )

        assert isinstance(app, FastAPI), "app must be an instance of FastAPI"
        assert len(app.routes) > 0, "FastAPI app must have registered routes"

    def test_tier2_all_expected_router_prefixes_registered(self):
        """Verify that all essential router endpoints/prefixes are registered on the app."""
        try:
            from app.main import app
        except Exception as exc:
            pytest.fail(f"FastAPI app import error: {exc}")

        registered_paths = []
        for r in app.routes:
            if hasattr(r, "path"):
                registered_paths.append(r.path)
            elif hasattr(r, "include_context") and hasattr(r.include_context, "prefix"):
                registered_paths.append(r.include_context.prefix)
        expected_prefixes = [
            "/api/ads",
            "/api/orders",
            "/api/products",
            "/api/auth",
            "/api/analytics",
            "/api/delivery-slots",
            "/api/delivery-charges",
            "/api/delivery-zones",
            "/api/returns",
            "/api/commission",
            "/api/tracking",
            "/api/users",
        ]

        missing_prefixes = []
        for prefix in expected_prefixes:
            has_prefix = any(p.startswith(prefix) for p in registered_paths)
            if not has_prefix:
                missing_prefixes.append(prefix)

        assert not missing_prefixes, (
            f"The following router prefixes are missing from the app routes: {missing_prefixes}"
        )

    def test_tier2_openapi_schema_generation(self):
        """Verify that app.openapi() generates a valid schema without Pydantic definition errors."""
        try:
            from app.main import app
        except Exception as exc:
            pytest.fail(f"FastAPI app import error: {exc}")

        openapi_schema = app.openapi()
        assert isinstance(openapi_schema, dict), "OpenAPI schema must be a dictionary"
        assert "openapi" in openapi_schema, "OpenAPI schema must declare 'openapi' version"
        assert "info" in openapi_schema, "OpenAPI schema must contain 'info' metadata"
        assert "paths" in openapi_schema, "OpenAPI schema must declare 'paths'"
        assert len(openapi_schema["paths"]) > 0, "OpenAPI paths must not be empty"


# ==============================================================================
# TIER 3: Endpoint Signature & Type Hint Check
# ==============================================================================


class TestTier3EndpointSignatures:
    """Tier 3: Endpoint signature check: assert no endpoint accepts raw payload: dict or data: dict."""

    def test_tier3_reference_router_ads_signatures(self):
        """Verify gold standard ads.py has no raw dict request body parameters."""
        ads_path = os.path.join(ROUTERS_DIR, "ads.py")
        violations = get_signature_violations_for_file(ads_path)
        assert len(violations) == 0, f"Gold standard ads.py has raw dict signature violations: {violations}"

    @pytest.mark.parametrize("router_filename", ACTIVE_ROUTER_FILES)
    def test_tier3_router_signatures_no_raw_dict(self, router_filename: str):
        """Verify that each router file has zero route handlers accepting raw dict payloads."""
        filepath = os.path.join(ROUTERS_DIR, router_filename)
        violations = get_signature_violations_for_file(filepath)

        if violations:
            formatted_violations = "\n".join(
                f"  - L{lineno} {func_name}(): parameter '{arg_name}: {ann}' -> '{line}'"
                for lineno, func_name, arg_name, ann, line in violations
            )
            pytest.fail(
                f"Router '{router_filename}' has {len(violations)} endpoint(s) accepting raw dict payload:\n"
                f"{formatted_violations}\n"
                f"Replace raw dict parameter with a strict Pydantic model (BaseModel subclass)."
            )

    def test_tier3_all_routers_aggregate_signatures(self):
        """Aggregate assertion verifying zero raw dict endpoint parameters across all routers."""
        all_violations: Dict[str, List[Tuple[int, str, str, str, str]]] = {}
        total_violations_count = 0

        for router_file in ACTIVE_ROUTER_FILES:
            filepath = os.path.join(ROUTERS_DIR, router_file)
            violations = get_signature_violations_for_file(filepath)
            if violations:
                all_violations[router_file] = violations
                total_violations_count += len(violations)

        if total_violations_count > 0:
            summary_lines = [
                f"Found {total_violations_count} route endpoint(s) with raw dict payloads across {len(all_violations)} files:"
            ]
            for r_file, viols in sorted(all_violations.items()):
                summary_lines.append(f"  - {r_file}: {len(viols)} signature violation(s)")
            pytest.fail("\n".join(summary_lines))


# ==============================================================================
# TIER 4: Pydantic Schema Validation & HTTP 422 Rejection
# ==============================================================================


# Target Pydantic DTO schemas defining the contract across refactored domains
class AdEventPayloadSchema(BaseModel):
    type: str


class AdStatusUpdateSchema(BaseModel):
    status: str


class AnalyticsEventPayloadSchema(BaseModel):
    type: str
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    page: str = "/"
    timestamp: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class NotifyPincodePayloadSchema(BaseModel):
    productId: str
    productName: str
    pincode: str
    email: Optional[str] = None


class Msg91WebhookPayloadSchema(BaseModel):
    Status: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None

    @property
    def resolved_status(self) -> Optional[str]:
        return self.Status or self.status or self.type


class RefreshTokenRequestSchema(BaseModel):
    userId: str
    sessionId: str
    refreshId: str


class DeliverySlotSchema(BaseModel):
    id: Optional[str] = None
    startTime: str
    endTime: str
    capacity: int = 10
    bookedCount: int = 0
    isFullDay: bool = False
    isUrgent: bool = False
    isActive: bool = True
    cutoffHours: Optional[int] = None
    urgentCutoffHours: Optional[int] = None


class DeliverySlotConfigCreateSchema(BaseModel):
    zoneId: str
    slots: List[DeliverySlotSchema] = Field(default_factory=list)
    zoneDefaultCapacity: int = 10


class ShippingAddressSchema(BaseModel):
    street: Optional[str] = None
    city: str
    state: str
    zipCode: str
    phone: Optional[str] = None


class OrderItemCreateSchema(BaseModel):
    productId: str
    quantity: int = Field(gt=0)
    price: float = Field(ge=0.0)


class CommissionTierSchema(BaseModel):
    id: Optional[str] = None
    minOrderValue: float = 0.0
    maxOrderValue: Optional[float] = None
    commissionPct: float = Field(ge=0.0, le=100.0)


class ReturnRequestCreateSchema(BaseModel):
    orderId: str
    reason: str
    items: List[Dict[str, Any]] = Field(default_factory=list)


class TestTier4SchemaValidationAndHttp422:
    """Tier 4: Validation test verifying Pydantic models reject invalid payloads with 422 / ValidationError and accept valid dot-notation schemas."""

    # --- Domain Model Validation & Dot-Notation Tests ---

    def test_tier4_ad_event_payload_validation(self):
        """AdEventPayload accepts valid event type via dot-notation, rejects missing required field."""
        valid = AdEventPayloadSchema(type="click")
        assert valid.type == "click"
        assert valid.model_dump() == {"type": "click"}

        with pytest.raises(ValidationError) as exc_info:
            AdEventPayloadSchema()
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("type",) for e in errors)

    def test_tier4_ad_status_update_validation(self):
        """AdStatusUpdate accepts valid status, rejects missing status."""
        valid = AdStatusUpdateSchema(status="active")
        assert valid.status == "active"

        with pytest.raises(ValidationError):
            AdStatusUpdateSchema()

    def test_tier4_analytics_event_payload_validation(self):
        """Analytics event model accepts typed fields with dot-notation, rejects missing required 'type'."""
        valid = AnalyticsEventPayloadSchema(
            type="product_view",
            sessionId="sess_123",
            payload={"productId": "prod_456", "returning": True},
        )
        assert valid.type == "product_view"
        assert valid.sessionId == "sess_123"
        assert valid.page == "/"
        assert valid.payload.get("productId") == "prod_456"

        with pytest.raises(ValidationError):
            AnalyticsEventPayloadSchema()  # type is required

    def test_tier4_notify_pincode_payload_validation(self):
        """NotifyPincodePayload accepts valid fields via dot-notation, rejects missing required fields."""
        valid = NotifyPincodePayloadSchema(
            productId="p100",
            productName="Pen Set",
            pincode="831001",
            email="user@test.com",
        )
        assert valid.product_id == "p100"
        assert valid.productName == "Pen Set"
        assert valid.pincode == "831001"
        assert valid.email == "user@test.com"

        # Missing required fields
        with pytest.raises(ValidationError):
            NotifyPincodePayloadSchema(productId="p100")

    def test_tier4_msg91_webhook_payload_validation(self):
        """Msg91WebhookPayload extracts status cleanly using dot-notation/properties."""
        payload1 = Msg91WebhookPayloadSchema(Status="delivered")
        assert payload1.resolved_status == "delivered"

        payload2 = Msg91WebhookPayloadSchema(status="sent")
        assert payload2.resolved_status == "sent"

        payload3 = Msg91WebhookPayloadSchema(type="failed")
        assert payload3.resolved_status == "failed"

    def test_tier4_refresh_token_payload_validation(self):
        """RefreshTokenRequest requires userId, sessionId, and refreshId."""
        valid = RefreshTokenRequestSchema(userId="u1", sessionId="s1", refreshId="r1")
        assert valid.userId == "u1"
        assert valid.sessionId == "s1"
        assert valid.refreshId == "r1"

        with pytest.raises(ValidationError):
            RefreshTokenRequestSchema(userId="u1")

    def test_tier4_delivery_slot_model_validation(self):
        """DeliverySlot model validates timing, capacity, and flags with dot-notation access."""
        slot = DeliverySlotSchema(
            id="slot_1",
            startTime="09:00",
            endTime="12:00",
            capacity=15,
            isUrgent=True,
        )
        assert slot.capacity == 15
        assert slot.isUrgent is True
        assert slot.isFullDay is False
        assert slot.startTime == "09:00"

        # Invalid capacity type string that cannot be parsed to int
        with pytest.raises(ValidationError):
            DeliverySlotSchema(startTime="09:00", endTime="12:00", capacity="not_an_int")

    def test_tier4_shipping_address_model_validation(self):
        """ShippingAddress model requires city, state, and zipCode; provides direct dot-notation."""
        addr = ShippingAddressSchema(
            city="Jamshedpur",
            state="Jharkhand",
            zipCode="831001",
            street="Main Road",
        )
        assert addr.city == "Jamshedpur"
        assert addr.state == "Jharkhand"
        assert addr.zipCode == "831001"
        assert addr.street == "Main Road"

        with pytest.raises(ValidationError):
            ShippingAddressSchema(street="Only street, missing city and state")

    def test_tier4_order_item_create_model_validation(self):
        """OrderItemCreate validates quantity > 0 and price >= 0."""
        item = OrderItemCreateSchema(productId="prod_1", quantity=3, price=49.99)
        assert item.product_id == "prod_1"
        assert item.quantity == 3
        assert item.price == 49.99

        # Quantity 0 or negative should fail validation
        with pytest.raises(ValidationError):
            OrderItemCreateSchema(productId="prod_1", quantity=0, price=10.0)

        with pytest.raises(ValidationError):
            OrderItemCreateSchema(productId="prod_1", quantity=-1, price=10.0)

    def test_tier4_commission_tier_model_validation(self):
        """CommissionTier validates numeric ranges and dot-notation access."""
        tier = CommissionTierSchema(id="tier_1", minOrderValue=0, maxOrderValue=1000, commissionPct=5.5)
        assert tier.minOrderValue == 0.0
        assert tier.maxOrderValue == 1000.0
        assert tier.commissionPct == 5.5

        # Commission percentage > 100 should fail validation
        with pytest.raises(ValidationError):
            CommissionTierSchema(commissionPct=150.0)

    def test_tier4_return_request_create_validation(self):
        """ReturnRequestCreate requires orderId and reason."""
        ret = ReturnRequestCreateSchema(orderId="ord_123", reason="Damaged item")
        assert ret.order_id == "ord_123"
        assert ret.reason == "Damaged item"

        with pytest.raises(ValidationError):
            ReturnRequestCreateSchema()

    # --- HTTP 422 Unprocessable Entity Rejection Integration Tests ---

    def test_tier4_fastapi_http_rejects_invalid_payload_with_422(self):
        """Test that FastAPI endpoints configured with strict Pydantic models return HTTP 422 on invalid payload."""
        test_app = FastAPI()
        test_router = APIRouter(prefix="/api/test-validation")

        @test_router.post("/ad-event")
        def create_ad_event(payload: AdEventPayloadSchema):
            return {"status": "ok", "type": payload.type}

        @test_router.post("/notify-pincode")
        def create_notify_pincode(payload: NotifyPincodePayloadSchema):
            return {"status": "ok", "productId": payload.product_id, "pincode": payload.pincode}

        test_app.include_router(test_router)
        client = TestClient(test_app)

        # 1. Send completely empty JSON body -> must return 422 Unprocessable Entity
        res_empty = client.post("/api/test-validation/ad-event", json={})
        assert res_empty.status_code == 422
        detail = res_empty.json().get("detail", [])
        assert len(detail) > 0, "422 response must contain validation error detail"
        assert any("type" in str(err.get("loc", [])) for err in detail)

        # 2. Send wrong data type for notify-pincode (missing required fields) -> must return 422
        res_missing = client.post(
            "/api/test-validation/notify-pincode",
            json={"productId": "p1"},  # missing productName, pincode
        )
        assert res_missing.status_code == 422
        detail_missing = res_missing.json().get("detail", [])
        loc_fields = [err.get("loc", [])[-1] for err in detail_missing if err.get("loc")]
        assert "productName" in loc_fields
        assert "pincode" in loc_fields

    def test_tier4_fastapi_http_accepts_valid_payload_and_uses_dot_notation(self):
        """Test that FastAPI endpoints accept valid payload and route handler processes fields via dot notation."""
        test_app = FastAPI()
        test_router = APIRouter(prefix="/api/test-validation")

        @test_router.post("/ad-event")
        def create_ad_event(payload: AdEventPayloadSchema):
            # Endpoint accesses payload via dot-notation (never payload.get())
            event_type = payload.type
            return {"status": "ok", "received_type": event_type}

        test_app.include_router(test_router)
        client = TestClient(test_app)

        valid_payload = {"type": "view"}
        res = client.post("/api/test-validation/ad-event", json=valid_payload)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("received_type") == "view"
