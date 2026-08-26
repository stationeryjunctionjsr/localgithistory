from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

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

    def _parse_date(self, date_str: str) -> datetime:
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.now(timezone.utc)

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
            if exclude_user_id and str(res.get("userId")) == str(exclude_user_id):
                continue

            # Check expiry
            expires_at = self._parse_date(res.get("expiresAt"))
            if expires_at > now:
                total += int(res.get("quantity", 0))

        return total

    async def get_user_reservations(self, user_id: str) -> List[Dict]:
        """Returns all active, non-expired reservations for a user."""
        await self.ensure_table_exists()
        all_res = await self.storage.findAll({"userId": str(user_id), "status": "active"})

        active_res = []
        now = datetime.now(timezone.utc)

        for res in all_res:
            expires_at = self._parse_date(res.get("expiresAt"))
            if expires_at > now:
                active_res.append(res)

        return active_res

    async def reserve_stock(self, product_id: str, user_id: str, quantity: int, ttl_minutes: int) -> Dict:
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
            await self.storage.update(res["_id"], {"status": "released"})
            logger.info("Released stock reservation %s for user %s", res["_id"], user_id)

    async def fulfill_user_reservations(self, user_id: str, product_id: Optional[str] = None):
        """Marks active reservations for a user as fulfilled (order placed)."""
        await self.ensure_table_exists()
        query = {"userId": str(user_id), "status": "active"}
        if product_id:
            query["productId"] = str(product_id)

        active_res = await self.storage.findAll(query)
        now = datetime.now(timezone.utc)

        for res in active_res:
            expires_at = self._parse_date(res.get("expiresAt"))
            # Only fulfill if not already expired
            if expires_at > now:
                await self.storage.update(res["_id"], {"status": "fulfilled"})
                logger.info("Fulfilled stock reservation %s for user %s", res["_id"], user_id)
            else:
                await self.storage.update(res["_id"], {"status": "expired"})

    async def cleanup_expired(self):
        """Finds and marks all expired reservations as 'expired'."""
        await self.ensure_table_exists()
        active_res = await self.storage.findAll({"status": "active"})

        now = datetime.now(timezone.utc)
        expired_count = 0

        for res in active_res:
            expires_at = self._parse_date(res.get("expiresAt"))
            if expires_at <= now:
                await self.storage.update(res["_id"], {"status": "expired"})
                expired_count += 1

        if expired_count > 0:
            logger.info("Cleaned up %d expired stock reservations", expired_count)

    async def reserve_stock_checked(self, product_id: str, user_id: str, quantity: int, ttl_minutes: int) -> dict:
        """Atomically check available stock and create a reservation in one transaction.

        Acquires a row-level lock on the product row (SELECT … FOR UPDATE) so that
        concurrent add-to-cart requests for the same product serialize here instead
        of racing through a check-then-act gap.

        Raises ValueError("Insufficient stock. Available: N") if stock is insufficient.
        Returns the created reservation dict on success.
        """
        import json
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import text

        from app.config.database import get_async_session_factory
        from app.db.storage_factory import get_storage as _get_storage

        await self.ensure_table_exists()
        factory = get_async_session_factory()
        if not factory:
            # Fallback: no DB factory — just do the non-atomic reserve (dev / test only)
            return await self.reserve_stock(product_id, user_id, quantity, ttl_minutes)

        product_storage = _get_storage("products")
        res_storage = self.storage

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        async with factory() as session:
            # 1. Lock the product row so no other request can read-and-decide simultaneously
            prod_result = await session.execute(
                text(f"SELECT id, doc FROM {product_storage.TABLE} WHERE external_id = :pid FOR UPDATE"),
                {"pid": str(product_id)},
            )
            prod_row = prod_result.fetchone()
            if not prod_row or not prod_row.doc:
                raise ValueError("Product not found")

            prod_doc = json.loads(prod_row.doc)
            actual_stock = int(prod_doc.get("stock", 0))

            # 2. Sum reservations held by OTHER users (within the same transaction)
            res_result = await session.execute(
                text(
                    f"SELECT doc FROM {res_storage.TABLE} "
                    f"WHERE JSON_UNQUOTE(JSON_EXTRACT(doc, '$.productId')) = :pid "
                    f"  AND JSON_UNQUOTE(JSON_EXTRACT(doc, '$.userId'))    != :uid "
                    f"  AND JSON_UNQUOTE(JSON_EXTRACT(doc, '$.status'))    = 'active' "
                    f"  AND JSON_UNQUOTE(JSON_EXTRACT(doc, '$.expiresAt')) > :now"
                ),
                {"pid": str(product_id), "uid": str(user_id), "now": now.isoformat()},
            )
            reserved_by_others = sum(int(json.loads(r.doc).get("quantity", 0)) for r in res_result.fetchall())

            available = actual_stock - reserved_by_others
            if available < quantity:
                raise ValueError(f"Insufficient stock. Available: {max(0, available)}")

            # 3. Release any existing active reservation of this user for this product
            old_res_result = await session.execute(
                text(
                    f"SELECT id FROM {res_storage.TABLE} "
                    f"WHERE JSON_UNQUOTE(JSON_EXTRACT(doc, '$.productId')) = :pid "
                    f"  AND JSON_UNQUOTE(JSON_EXTRACT(doc, '$.userId'))    = :uid "
                    f"  AND JSON_UNQUOTE(JSON_EXTRACT(doc, '$.status'))    = 'active'"
                ),
                {"pid": str(product_id), "uid": str(user_id)},
            )
            for old_row in old_res_result.fetchall():
                released_doc = {"status": "released", "updatedAt": now.isoformat()}
                await session.execute(
                    text(
                        f"UPDATE {res_storage.TABLE} "
                        f"SET doc = JSON_MERGE_PATCH(doc, :patch), updated_at = UTC_TIMESTAMP() "
                        f"WHERE id = :rid"
                    ),
                    {"patch": json.dumps(released_doc), "rid": old_row.id},
                )

            # 4. Insert new reservation
            import secrets

            external_id = secrets.token_hex(16)
            reservation_data = {
                "productId": str(product_id),
                "userId": str(user_id),
                "quantity": int(quantity),
                "status": "active",
                "expiresAt": expires_at.isoformat() + "Z",
            }
            await session.execute(
                text(
                    f"INSERT INTO {res_storage.TABLE} (external_id, doc, created_at, updated_at) "
                    f"VALUES (:eid, :doc, UTC_TIMESTAMP(), UTC_TIMESTAMP())"
                ),
                {"eid": external_id, "doc": json.dumps(reservation_data)},
            )

            await session.commit()

        reservation_data["_id"] = external_id
        return reservation_data


# Global singleton instance
stock_reservation_repository = StockReservationRepository()
