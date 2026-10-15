import typing
from unittest.mock import MagicMock, patch
import pytest

from app.models.user import User
from app.services.email_service import EmailService
from app.routers.analytics import _resolve_seller_id
from app.utils.auth import require_roles


def test_issue11_email_service_type_hints_reflection_and_resolve_to_emails():
    """Verify typing.get_type_hints works without NameError and _resolve_to_emails resolves properly."""
    # 1. Reflection check: get_type_hints must not raise NameError
    hints = typing.get_type_hints(EmailService.send_error_alert)
    assert "to_emails" in hints
    assert "return" in hints
    assert hints["return"] is bool

    # 2. _resolve_to_emails verification
    service = EmailService()
    service.admin_emails = ["admin1@example.com", "admin2@example.com"]

    # None defaults to admin_emails
    assert service._resolve_to_emails(None) == ["admin1@example.com", "admin2@example.com"]

    # Single string
    assert service._resolve_to_emails("ops@example.com") == ["ops@example.com"]

    # Comma-separated string
    assert service._resolve_to_emails("ops1@example.com, ops2@example.com ") == [
        "ops1@example.com",
        "ops2@example.com",
    ]

    # List of strings
    assert service._resolve_to_emails(["dev@example.com ", " alerts@example.com"]) == [
        "dev@example.com",
        "alerts@example.com",
    ]


@pytest.mark.asyncio
async def test_issue12_seller_analytics_scoping_and_roles():
    """Verify _resolve_seller_id scopes sellers correctly and require_roles permits role='seller'."""
    seller_user = User(
        id=42,
        email="seller@example.com",
        role="seller",
        is_active=True,
    )

    wholesaler_user = User(
        id=77,
        email="wholesaler@example.com",
        role="wholesaler",
        is_active=True,
    )

    admin_user = User(
        id=1,
        email="admin@example.com",
        role="super_admin",
        is_active=True,
    )

    # 1. Scoping checks
    # Seller should always scope to their own ID regardless of requested_seller_id
    assert _resolve_seller_id(seller_user, requested_seller_id=999) == 42
    assert _resolve_seller_id(seller_user, requested_seller_id=None) == 42

    # Wholesaler should always scope to their own ID
    assert _resolve_seller_id(wholesaler_user, requested_seller_id=999) == 77

    # Super admin can filter by requested seller_id or view all (None)
    assert _resolve_seller_id(admin_user, requested_seller_id=999) == 999
    assert _resolve_seller_id(admin_user, requested_seller_id=None) is None

    # 2. Dependency authorization check: check_roles and require_roles("super_admin", "wholesaler", "seller")
    from app.utils.auth import check_roles
    roles = ("super_admin", "wholesaler", "seller")

    allowed_seller = check_roles(seller_user, *roles)
    assert allowed_seller.id == 42
    assert allowed_seller.role == "seller"

    allowed_wholesaler = check_roles(wholesaler_user, *roles)
    assert allowed_wholesaler.id == 77

    allowed_admin = check_roles(admin_user, *roles)
    assert allowed_admin.id == 1

    # Unauthorized role (e.g. regular customer) should raise HTTPException(403)
    customer_user = User(
        id=10,
        email="customer@example.com",
        role="customer",
        is_active=True,
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        check_roles(customer_user, *roles)
    assert exc_info.value.status_code == 403

    # Also test role_checker via dependency injection with mocked verify_token
    role_checker = require_roles("super_admin", "wholesaler", "seller")
    mock_request = MagicMock()
    with patch("app.utils.auth._extract_token", return_value="valid_token"):
        with patch("app.utils.auth.verify_token", return_value=seller_user):
            dep_seller = await role_checker(request=mock_request, credentials=None)
            assert dep_seller.id == 42
            assert dep_seller.role == "seller"
