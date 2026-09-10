from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from app.db.storage_factory import get_storage

# ── ORACLE-specific imports (commented out — Oracle disabled) ──────────────────
# from app.config.database import use_oracle, get_async_session_factory
# ─────────────────────────────────────────────────────────────────────────
from app.utils.logger import logger


class StockReservationRepository:
    def __init__(self):
        # We wrap storage retrieval in a property or get it dynamically
        self._storage = None
        self._initialized = False

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage("stockReservations")
        return self._storage

    async def ensure_table_exists(self):
        if self._initialized:
            return
        # MySQL: tables are created by Alembic migrations — no runtime DDL needed.
        self._initialized = True

        # ── ORACLE runtime table creation (commented out) ────────────────────────
        # if not use_oracle():
        #     self._initialized = True
        #     return
        # ... (Oracle CREATE TABLE for sj_stock_reservations)
        # ─────────────────────────────────────────────────────────────────────────

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat() + "Z"

    async def get_reserved_quantity(self, product_id: str, exclude_user_id: Optional[str] = None) -> int:
        """Returns the total active, non-expired reserved quantity for a product."""
        await self.ensure_table_exists()
        # Find all active reservations
        all_res = await self.storage.findAll({"productId": str(product_id), "status": "active"})

        total = 0
        now = datetime.now(timezone.utc)

        for res in all_res:
            if exclude_user_id and str(res.user_id) == str(exclude_user_id):
                continue

            # Check expiry
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) > now:
                total += int(res.quantity)

        return total

    async def get_user_reservations(self, user_id: str) -> List[Any]:
        """Returns all active, non-expired reservations for a user."""
        await self.ensure_table_exists()
        all_res = await self.storage.findAll({"userId": str(user_id), "status": "active"})

        active_res = []
        now = datetime.now(timezone.utc)

        for res in all_res:
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) > now:
                active_res.append(res)

        return active_res

    async def reserve_stock(self, product_id: str, user_id: str, quantity: int, ttl_minutes: int) -> Any:
        """Creates or updates a reservation for a product and user."""
        await self.ensure_table_exists()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        # Release any existing active reservation of this user for this product first
        await self.release_user_reservations(user_id, product_id)

        reservation_data = {
            "productId": str(product_id),
            "userId": str(user_id),
            "quantity": int(quantity),
            "status": "active",
            "expiresAt": expires_at.isoformat() + "Z",
        }

        created = await self.storage.create(reservation_data)
        logger.info(
            "Created stock reservation for user %s, product %s, qty %d (expires in %d min)",
            user_id,
            product_id,
            quantity,
            ttl_minutes,
        )
        return created

    async def release_user_reservations(self, user_id: str, product_id: Optional[str] = None):
        """Marks active reservations for a user as released."""
        await self.ensure_table_exists()
        query = {"userId": str(user_id), "status": "active"}
        if product_id:
            query["productId"] = str(product_id)

        active_res = await self.storage.findAll(query)
        for res in active_res:
            await self.storage.update(str(res.id), {"status": "released"})
            logger.info("Released stock reservation %s for user %s", res.id, user_id)

    async def fulfill_user_reservations(self, user_id: str, product_id: Optional[str] = None):
        """Marks active reservations for a user as fulfilled (order placed)."""
        await self.ensure_table_exists()
        query = {"userId": str(user_id), "status": "active"}
        if product_id:
            query["productId"] = str(product_id)

        active_res = await self.storage.findAll(query)
        now = datetime.now(timezone.utc)

        for res in active_res:
            # Only fulfill if not already expired
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) > now:
                await self.storage.update(str(res.id), {"status": "fulfilled"})
                logger.info("Fulfilled stock reservation %s for user %s", res.id, user_id)
            else:
                await self.storage.update(str(res.id), {"status": "expired"})

    async def cleanup_expired(self):
        """Finds and marks all expired reservations as 'expired'."""
        await self.ensure_table_exists()
        active_res = await self.storage.findAll({"status": "active"})

        now = datetime.now(timezone.utc)
        expired_count = 0

        for res in active_res:
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) <= now:
                await self.storage.update(str(res.id), {"status": "expired"})
                expired_count += 1

        if expired_count > 0:
            logger.info("Cleaned up %d expired stock reservations", expired_count)

    async def reserve_stock_checked(self, product_id: str, user_id: str, quantity: int, ttl_minutes: int) -> dict:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import text
        from app.config.database import get_async_session_factory
        from app.db.storage_factory import get_storage as _get_storage

        await self.ensure_table_exists()
        factory = get_async_session_factory()
        if not factory:
            return await self.reserve_stock(product_id, user_id, quantity, ttl_minutes)

        product_storage = _get_storage("products")
        res_storage = self.storage

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        async with factory() as session:
            # 1. Lock the product row
            prod_result = await session.execute(
                text(f"SELECT id, stock FROM {product_storage.TABLE} WHERE id = :pid FOR UPDATE"),
                {"pid": str(product_id)},
            )
            prod_row = prod_result.fetchone()
            if not prod_row:
                raise ValueError("Product not found")

            actual_stock = int(prod_row.stock)

            # 2. Sum reservations held by OTHER users
            res_result = await session.execute(
                text(
                    f"SELECT SUM(quantity) as reserved FROM {res_storage.TABLE} "
                    f"WHERE product_id = :pid "
                    f"  AND user_id != :uid "
                    f"  AND status = 'active' "
                    f"  AND expires_at > :now"
                ),
                {"pid": str(product_id), "uid": str(user_id), "now": now.replace(tzinfo=None)},
            )
            res_row = res_result.fetchone()
            other_reserved = int(res_row.reserved or 0) if res_row else 0

            available = max(0, actual_stock - other_reserved)
            if available < quantity:
                raise ValueError(f"Insufficient stock. Available: {available}")

            # 3. All clear, make the reservation
            return await self.reserve_stock(product_id, user_id, quantity, ttl_minutes)

stock_reservation_repository = StockReservationRepository()
