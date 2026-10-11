import logging
"""
MySQL DAO for payments: sj_payments (header) + sj_payment_entries (child rows).
Assembles paymentEntries from child table; create/update write entries as separate rows.
"""

import secrets
from datetime import datetime, date
from app.models.payment import Payment, PaymentEntry, List, Optional

from sqlalchemy import bindparam, text
from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


def _to_ts(val):
    if val is None:
        return None
    if type(val) in (datetime, date):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception as e:
        logging.warning("mysql_payment_dao._to_ts: could not parse timestamp %r: %s", val, e, exc_info=e)
        return None


def _entry__map_to_schema(er) -> PaymentEntry:
    return PaymentEntry(
        entryId=er.entry_id,
        amount=float(er.amount) if er.amount is not None else 0,
        paymentMethod=er.payment_method,
        paidAt=er.paid_at.isoformat() if er.paid_at and type(er.paid_at) in (datetime, date) else (str(er.paid_at) if er.paid_at else None),
        image=er.image,
        notes=er.notes,
        verified=bool(er.verified) if er.verified is not None else False,
        createdAt=er.created_at.isoformat() if er.created_at and type(er.created_at) in (datetime, date) else (str(er.created_at) if er.created_at else None),
    )


def _payment__map_to_schema(r, entries: List[PaymentEntry]) -> Payment:
    return Payment(
        id=str(r.id),
        order_id=r.order_id,
        userId=r.user_id,
        userIdFormatted=r.user_id_formatted,
        customerName=r.customer_name,
        orderDate=r.order_date.isoformat() if r.order_date else None,
        payment_method=r.payment_method,
        amountPaid=float(r.amount_paid) if r.amount_paid is not None else None,
        amountRemaining=float(r.amount_remaining) if r.amount_remaining is not None else None,
        totalAmount=float(r.total_amount) if r.total_amount is not None else None,
        paymentId=r.payment_id,
        paymentEntries=entries,
        created_at=r.created_at.isoformat() if r.created_at else None,
        updated_at=r.updated_at.isoformat() if r.updated_at else None,
    )


class MySQLPaymentDAO:
    @property
    def PAYMENTS_TABLE(self):
        return "sj_payments"

    @property
    def ENTRIES_TABLE(self):
        return "sj_payment_entries"

    def _factory(self):
        return get_async_session_factory()

    async def _get_entries_for_payment_ids(self, session, payment_ids: List[int]) -> list:
        if not payment_ids:
            return []
        stmt = text(
            f"SELECT payment_id, entry_id, amount, payment_method, paid_at, image, notes, verified, created_at "
            f"FROM {self.ENTRIES_TABLE} WHERE payment_id IN :ids ORDER BY payment_id, entry_id"
        ).bindparams(bindparam("ids", expanding=True))
        result = await session.execute(stmt, {"ids": list(payment_ids)})
        return result.fetchall()

    async def findAll(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
        allowed_order_ids: Optional[List[str]] = None,
    ) -> List[Payment]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if order_id is not None:
            where_clauses.append("order_id = :order_id")
            params["order_id"] = order_id
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if allowed_order_ids is not None:
            if not allowed_order_ids:
                where_clauses.append("1=0")
            else:
                chunks = [allowed_order_ids[i : i + 999] for i in range(0, len(allowed_order_ids), 999)]
                chunk_sqls = []
                for chunk_idx, chunk in enumerate(chunks):
                    id_params = {f"aoid_{chunk_idx}_{i}": oid for i, oid in enumerate(chunk)}
                    params.update(id_params)
                    id_placeholders = ", ".join([f":{k}" for k in id_params.keys()])
                    chunk_sqls.append(f"order_id IN ({id_placeholders})")

                if len(chunk_sqls) == 1:
                    where_clauses.append(chunk_sqls[0])
                else:
                    where_clauses.append("(" + " OR ".join(chunk_sqls) + ")")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, order_id, user_id, user_id_formatted, customer_name, order_date, "
                    f"payment_method, amount_paid, amount_remaining, total_amount, payment_id, created_at, updated_at "
                    f"FROM {self.PAYMENTS_TABLE} "
                    f"WHERE {where_sql} "
                    f"ORDER BY id ASC"
                ),
                params,
            )
            rows = result.fetchall()
        if not rows:
            return []
        ids = [r.id for r in rows]
        async with factory() as session:
            entry_rows = await self._get_entries_for_payment_ids(session, ids)
        records = []
        for r in rows:
            entries = [
                _entry__map_to_schema(er)
                for er in entry_rows
                if er.payment_id == r.id
            ]
            records.append(_payment__map_to_schema(r, entries))
        return records

    async def findById(self, id: str) -> Optional[Payment]:
        factory = self._factory()
        if not factory:
            return None
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, order_id, user_id, user_id_formatted, customer_name, order_date, "
                    f"payment_method, amount_paid, amount_remaining, total_amount, payment_id, created_at, updated_at "
                    f"FROM {self.PAYMENTS_TABLE} WHERE id = :id"
                ),
                {"id": pid},
            )
            row = result.fetchone()
        if not row:
            return None
        async with factory() as session:
            entry_rows = await self._get_entries_for_payment_ids(session, [pid])
        entries = [
            _entry__map_to_schema(er)
            for er in entry_rows
            if er.payment_id == pid
        ]
        return _payment__map_to_schema(row, entries)

    async def findOne(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Payment]:
        records = await self.findAll(order_id=order_id, user_id=user_id)
        return records[0] if records else None

    async def create(self, data: PaymentInternalCreate) -> Payment:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        payment_entries = data.payment_entries or []
        params = {
            "external_id": external_id,
            "order_id": data.order_id,
            "user_id": data.user_id,
            "user_id_formatted": data.user_id_formatted,
            "customer_name": data.customer_name,
            "order_date": _to_ts(data.order_date) or now,
            "payment_method": data.payment_method,
            "amount_paid": data.amount_paid,
            "amount_remaining": data.amount_remaining,
            "total_amount": data.total_amount,
            "payment_id": data.payment_id,
            "created_at": now,
            "updated_at": now,
        }
        async with factory() as session:
            await session.execute(
                text(
                    f"INSERT INTO {self.PAYMENTS_TABLE} (external_id, order_id, user_id, user_id_formatted, "
                    f"customer_name, order_date, payment_method, amount_paid, amount_remaining, total_amount, "
                    f"payment_id, created_at, updated_at) VALUES (:external_id, :order_id, :user_id, :user_id_formatted, "
                    f":customer_name, :order_date, :payment_method, :amount_paid, :amount_remaining, :total_amount, "
                    f":payment_id, :created_at, :updated_at)"
                ),
                params,
            )
            await session.commit()
            result = await session.execute(
                text(f"SELECT id FROM {self.PAYMENTS_TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = result.scalar()
        if new_id and payment_entries:
            async with factory() as session:
                for idx, entry in enumerate(payment_entries):
                    entry_id = (entry.entry_id if entry.entry_id is not None else idx + 1)
                    amount = (entry.amount if entry.amount is not None else 0)
                    method = entry.payment_method or data.payment_method
                    paid_at = _to_ts(entry.paid_at) or now
                    await session.execute(
                        text(
                            f"INSERT INTO {self.ENTRIES_TABLE} (payment_id, entry_id, amount, payment_method, paid_at, image, notes, verified, created_at) "
                            f"VALUES (:payment_id, :entry_id, :amount, :payment_method, :paid_at, :image, :notes, :verified, :created_at)"
                        ),
                        {
                            "payment_id": new_id,
                            "entry_id": entry_id,
                            "amount": amount,
                            "payment_method": method,
                            "paid_at": paid_at,
                            "image": entry.image,
                            "notes": (entry.notes if entry.notes is not None else ""),
                            "verified": 1 if (entry.verified if entry.verified is not None else False) else 0,
                            "created_at": now,
                        },
                    )
                await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: PaymentInternalUpdate) -> Optional[Payment]:
        existing = await self.findById(id)
        if not existing:
            return None
        resolved_order_id = update_data.order_id if update_data.order_id is not None else existing.order_id
        resolved_user_id = update_data.user_id if update_data.user_id is not None else existing.user_id
        resolved_user_id_fmt = update_data.user_id_formatted if update_data.user_id_formatted is not None else existing.user_id_formatted
        resolved_customer_name = update_data.customer_name if update_data.customer_name is not None else existing.customer_name
        resolved_order_date = update_data.order_date if update_data.order_date is not None else existing.order_date
        resolved_payment_method = update_data.payment_method if update_data.payment_method is not None else existing.payment_method
        resolved_amount_paid = update_data.amount_paid if update_data.amount_paid is not None else existing.amount_paid
        resolved_amount_remaining = update_data.amount_remaining if update_data.amount_remaining is not None else existing.amount_remaining
        resolved_total_amount = update_data.total_amount if update_data.total_amount is not None else existing.total_amount
        resolved_payment_id = update_data.payment_id if update_data.payment_id is not None else existing.payment_id

        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(
                    f"UPDATE {self.PAYMENTS_TABLE} SET order_id=:order_id, user_id=:user_id, user_id_formatted=:user_id_formatted, "
                    f"customer_name=:customer_name, order_date=:order_date, payment_method=:payment_method, "
                    f"amount_paid=:amount_paid, amount_remaining=:amount_remaining, total_amount=:total_amount, "
                    f"payment_id=:payment_id, updated_at=:updated_at WHERE id=:id"
                ),
                {
                    "order_id": resolved_order_id,
                    "user_id": resolved_user_id,
                    "user_id_formatted": resolved_user_id_fmt,
                    "customer_name": resolved_customer_name,
                    "order_date": _to_ts(resolved_order_date),
                    "payment_method": resolved_payment_method,
                    "amount_paid": resolved_amount_paid,
                    "amount_remaining": resolved_amount_remaining,
                    "total_amount": resolved_total_amount,
                    "payment_id": resolved_payment_id,
                    "updated_at": now,
                    "id": pid,
                },
            )
            await session.commit()
            if update_data.payment_entries is not None:
                await session.execute(text(f"DELETE FROM {self.ENTRIES_TABLE} WHERE payment_id = :id"), {"id": pid})
                await session.commit()
                for idx, entry in enumerate(update_data.payment_entries):
                    entry_id = (entry.entry_id if entry.entry_id is not None else idx + 1)
                    paid_at = _to_ts(entry.paid_at) or now
                    await session.execute(
                        text(
                            f"INSERT INTO {self.ENTRIES_TABLE} (payment_id, entry_id, amount, payment_method, paid_at, image, notes, verified, created_at) "
                            f"VALUES (:payment_id, :entry_id, :amount, :payment_method, :paid_at, :image, :notes, :verified, :created_at)"
                        ),
                        {
                            "payment_id": pid,
                            "entry_id": entry_id,
                            "amount": (entry.amount if entry.amount is not None else 0),
                            "payment_method": entry.payment_method or resolved_payment_method,
                            "paid_at": paid_at,
                            "image": entry.image,
                            "notes": (entry.notes if entry.notes is not None else ""),
                            "verified": 1 if (entry.verified if entry.verified is not None else False) else None,
                            "created_at": now,
                        },
                    )
                await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(text(f"DELETE FROM {self.ENTRIES_TABLE} WHERE payment_id = :id"), {"id": pid})
            result = await session.execute(text(f"DELETE FROM {self.PAYMENTS_TABLE} WHERE id = :id"), {"id": pid})
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        records = await self.findAll(order_id=order_id, user_id=user_id)
        deleted = 0
        for r in records:
            if await self.delete(r.id):
                deleted += 1
        return deleted

    async def count(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        return len(await self.findAll(order_id=order_id, user_id=user_id))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
