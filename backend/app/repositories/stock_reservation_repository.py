from app.models.daos_flat import StockReservationsInternalUpdate
from datetime import datetime, timedelta, timezone
from typing import List, Optional

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

    async def get_user_reservations(self, user_id: str) -> List['StockReservationInternal']:
        """Returns all active, non-expired reservations for a user."""
        await self.ensure_table_exists()
        all_res = await self.storage.findAll({"userId": str(user_id), "status": "active"})

        active_res = []
        now = datetime.now(timezone.utc)

        for res in all_res:
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) > now:
                active_res.append(res)

        return active_res

    async def reserve_stock(self, product_id: str, user_id: str, quantity: int, ttl_minutes: int) -> dict:
        """Creates or updates a reservation for a product and user."""
        await self.ensure_table_exists()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        # Release any existing active reservation of this user for this product first
        await self.release_user_reservations(user_id, product_id)

        from app.models.daos_flat import StockReservationsInternalCreate
        reservation_data = StockReservationsInternalCreate(
            product_id=str(product_id),
            user_id=str(user_id),
            quantity=int(quantity),
            status="active",
            expires_at=expires_at.isoformat() + "Z",
        )

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
            await self.storage.update(str(res.id), StockReservationsInternalUpdate(status="released"))
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
                await self.storage.update(str(res.id), StockReservationsInternalUpdate(status="fulfilled"))
                logger.info("Fulfilled stock reservation %s for user %s", res.id, user_id)
            else:
                await self.storage.update(str(res.id), StockReservationsInternalUpdate(status="expired"))

    async def cleanup_expired(self):
        """Finds and marks all expired reservations as 'expired'."""
        await self.ensure_table_exists()
        active_res = await self.storage.findAll({"status": "active"})

        now = datetime.now(timezone.utc)
        expired_count = 0

        for res in active_res:
            if res.expires_at and res.expires_at.replace(tzinfo=timezone.utc) <= now:
                await self.storage.update(str(res.id), StockReservationsInternalUpdate(status="expired"))
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
        now_naive = now.replace(tzinfo=None)
        expires_at = now + timedelta(minutes=ttl_minutes)
        expires_naive = expires_at.replace(tzinfo=None)

        async with factory() as session:
            # 1. Lock the product row — serialises concurrent add-to-cart for same product.
            prod_result = await session.execute(
                text(f"SELECT id, stock FROM {product_storage.TABLE} WHERE id = :pid FOR UPDATE"),
                {"pid": str(product_id)},
            )
            prod_row = prod_result.fetchone()
            if not prod_row:
                raise ValueError("Product not found")

            actual_stock = int(prod_row.stock)

            # 2. Sum reservations held by OTHER users (inside same transaction).
            res_result = await session.execute(
                text(
                    f"SELECT SUM(quantity) as reserved FROM {res_storage.TABLE} "
                    f"WHERE product_id = :pid "
                    f"  AND user_id != :uid "
                    f"  AND status = 'active' "
                    f"  AND expires_at > :now"
                ),
                {"pid": str(product_id), "uid": str(user_id), "now": now_naive},
            )
            res_row = res_result.fetchone()
            other_reserved = int(res_row.reserved or 0) if res_row else 0

            available = max(0, actual_stock - other_reserved)
            if available < quantity:
                raise ValueError(f"Insufficient stock. Available: {available}")

            # 3. Release any existing active reservation for this user+product.
            #    Uses the SAME connection — no second pool slot needed while FOR UPDATE is held.
            await session.execute(
                text(
                    f"UPDATE {res_storage.TABLE} "
                    f"SET status = 'released', updated_at = UTC_TIMESTAMP() "
                    f"WHERE product_id = :pid AND user_id = :uid AND status = 'active'"
                ),
                {"pid": str(product_id), "uid": str(user_id)},
            )

            # 4. Insert new reservation in the same connection (eliminates the deadlock risk).
            import secrets as _secrets
            ext_id = _secrets.token_hex(16)
            await session.execute(
                text(
                    f"INSERT INTO {res_storage.TABLE} "
                    f"(external_id, product_id, user_id, quantity, status, expires_at, created_at, updated_at) "
                    f"VALUES (:eid, :pid, :uid, :qty, 'active', :exp, :now, :now)"
                ),
                {
                    "eid": ext_id,
                    "pid": str(product_id),
                    "uid": str(user_id),
                    "qty": int(quantity),
                    "exp": expires_naive,
                    "now": now_naive,
                },
            )
            new_id_row = await session.execute(
                text(f"SELECT id FROM {res_storage.TABLE} WHERE external_id = :eid"),
                {"eid": ext_id},
            )
            new_id = new_id_row.scalar()
            await session.commit()

        logger.info(
            "Created stock reservation (atomic) for user %s, product %s, qty %d (expires in %d min)",
            user_id,
            product_id,
            quantity,
            ttl_minutes,
        )
        return await self.storage.findById(str(new_id))


# ── MULTI-VM STOCK RESERVATION (commented out — already handled by DB-level lock) ──
#
# The active reserve_stock_checked() above uses SELECT … FOR UPDATE on the product
# row.  This is a MySQL row lock — it serialises concurrent requests from ALL
# uvicorn workers across ALL VMs that share the same database, so no extra
# distributed locking layer is required today.
#
# HOW SINGLE-VM WORKS (active):
#   Within one VM, uvicorn runs N workers (processes).  Each worker independently
#   calls reserve_stock_checked().  MySQL's FOR UPDATE ensures only one worker
#   at a time can read-check-update the product row, regardless of N.
#
# IF EXTREME PRE-DB LOAD SHEDDING IS EVER NEEDED (multi-VM, high RPS):
#   Replace the `async with factory() as session:` block with a Redis distributed
#   lock so only one request per product_id even reaches MySQL at a time:
#
# # async def reserve_stock_checked_redis_gated(
# #     self, product_id: str, user_id: str, quantity: int, ttl_minutes: int
# # ) -> dict:
# #     """Like reserve_stock_checked but gates via a Redis distributed lock.
# #     Use when DB FOR UPDATE queuing is acceptable but pre-DB load shedding
# #     is needed under extreme concurrency (e.g. flash-sale traffic).
# #     """
# #     import aioredis
# #     redis = aioredis.from_url(os.environ["REDIS_URL"])
# #     lock_key = f"sj:reserve:{product_id}"
# #     async with redis.lock(lock_key, timeout=10, blocking_timeout=8):
# #         return await self.reserve_stock_checked(product_id, user_id, quantity, ttl_minutes)
#
# TO ACTIVATE:
#   1. pip install aioredis
#   2. Add REDIS_URL to .env
#   3. Rename above to reserve_stock_checked; retire the current one.
#   4. All callers (orders.py) pick it up automatically.
#
# ────────────────────────────────────────────────────────────────────────────────────

stock_reservation_repository = StockReservationRepository()
