"""
Admin audit decorator — attaches to admin mutation endpoints to log
who did what to which entity.

Usage:
    @router.put("/{user_id}/approve", response_model=UserResponse)
    @audit_action("user", "approve")
    async def approve_user(user_id: str, current_user: User = Depends(require_roles("super_admin")), request: Request = None):
        ...

The decorator extracts `request` (for IP), `current_user` (actor), and any
path-parameter named `*_id` / `id` (entity_id) from the wrapped function's
arguments at call time.  It fires the audit write AFTER the handler succeeds
(no audit row on exception).
"""

import functools
import inspect
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def audit_action(entity_type: str, action: str) -> Callable:
    """
    Decorator factory.  Wraps an async FastAPI endpoint and writes one
    admin audit row after the handler returns successfully.

    Args:
        entity_type: Logical entity being mutated, e.g. "user", "product", "coupon".
        action:      Verb describing the mutation, e.g. "approve", "delete", "role_change".
    """
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # ── Resolve call-site values from kwargs/bound args ──────────────
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            call_args: dict = bound.arguments

            # Actor — any param typed as or named current_user
            current_user = call_args.get("current_user")
            actor_id: Optional[str] = str(current_user.id) if current_user is not None else None
            actor_role: Optional[str] = (
                current_user.effective_role or current_user.role
            ) if current_user is not None else None

            # Entity ID — prefer explicit path params ending in _id or named id
            entity_id: Optional[str] = None
            for param_name, param_value in call_args.items():
                if param_name in ("user_id", "product_id", "coupon_id", "order_id",
                                  "category_id", "brand_id", "entity_id", "id"):
                    entity_id = str(param_value) if param_value is not None else None
                    break

            # IP address
            request = call_args.get("request")
            ip_address: Optional[str] = None
            if request is not None:
                try:
                    ip_address = request.client.host if request.client else None
                except Exception:
                    pass

            # Write asynchronously — never raise on failure
            try:
                from app.db.mysql_admin_audit_dao import admin_audit_dao
                await admin_audit_dao.log(
                    actor_id=actor_id or "unknown",
                    actor_role=actor_role or "unknown",
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    change_summary=None,  # Body payload not captured to avoid logging PII
                    ip_address=ip_address,
                )
            except Exception as exc:
                logger.error(
                    "audit_action: unexpected error writing audit row: %s", exc, exc_info=True
                )

            return result

        return wrapper
    return decorator
