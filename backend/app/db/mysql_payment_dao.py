import logging
"""
MySQL DAO for payments: sj_payments (header) + sj_payment_entries (child rows).
Assembles paymentEntries from child table; create/update write entries as separate rows.
"""

import secrets
from datetime import datetime, date
from typing import Dict
from app.models.payment import Payment, List, Optional

from sqlalchemy import bindparam, text
from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


def _to_ts(val):
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception as e:
        logging.warning("mysql_payment_dao._to_ts: could not parse timestamp %r: %s", val, e, exc_info=e)
        return None


from app.models.payment import PaymentEntry

def _entry__map_to_schema(entry_id, amount, payment_method, paid_at, image, notes, verified, created_at) -> PaymentEntry:
    return PaymentEntry(
        entryId=entry_id,
        amount=float(amount) if amount is not None else 0,
        paymentMethod=payment_method,
        paidAt=paid_at.isoformat() if isinstance(paid_at, (datetime, date)) and paid_at else None,
        image=image,
        notes=notes,
        verified=bool(verified) if verified is not None else False,
        createdAt=created_at.isoformat() if isinstance(created_at, (datetime, date)) and created_at else None,
    )


def _payment__map_to_schema(r, entries: List[PaymentEntry]) -> Payment:
    return Payment(**{
        "_id": str(r.id),
        "orderId": r.order_id,
        "userId": r.user_id,
        "userIdFormatted": r.user_id_formatted,
        "customerName": r.customer_name,
        "orderDate": r.order_date.isoformat() if r.order_date else None,
        "paymentMethod": r.payment_method,
        "amountPaid": float(r.amount_paid) if r.amount_paid is not None else None,
        "amountRemaining": float(r.amount_remaining) if r.amount_remaining is not None else None,
        "totalAmount": float(r.total_amount) if r.total_amount is not None else None,
        "paymentId": r.payment_id,
        "paymentEntries": entries,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
    })


class MySQLPaymentDAO:
    @property
    def PAYMENTS_TABLE(self):
        return "sj_payments"

    @property
    def ENTRIES_TABLE(self):
        return "sj_payment_entries"

    def _factory(self):
        return get_async_session_factory()

    async def _get_entries_for_payment_ids(self, session, payment_ids: List[int]) -> Dict[int, List[Dict]]:
        if not payment_ids:
            return {}
        stmt = text(
            f"SELECT payment_id, entry_id, amount, payment_method, paid_at, image, notes, verified, created_at "
            f"FROM {self.ENTRIES_TABLE} WHERE payment_id IN :ids ORDER BY payment_id, entry_id"
        ).bindparams(bindparam("ids", expanding=True))
        result = await session.execute(stmt, {"ids": list(payment_ids)})
        rows = result.fetchall()
        by_payment = {}
        for r in rows:
            pid = r[0]
            if pid not in by_payment:
                by_payment[pid] = []
            by_payment[pid].append(_entry__map_to_schema(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
        return by_payment

    async def findAll(self, query: Optional[Dict] = None) -> List[Payment]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            if "orderId" in query and query["orderId"]:
                where_clauses.append("order_id = :order_id")
                params["order_id"] = query["orderId"]
            if "userId" in query and query["userId"]:
                where_clauses.append("user_id = :user_id")
                params["user_id"] = query["userId"]
            if "allowed_order_ids" in query:
                allowed_order_ids = query["allowed_order_ids"]
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
        ids = [r[0] for r in rows]
        async with factory() as session:
            entries_by_payment = await self._get_entries_for_payment_ids(session, ids)
        Cols = type("Cols", (), {})
        docs = []
        for r in rows:
            (
                id_,
                ext,
                order_id,
                user_id,
                user_id_fmt,
                customer_name,
                order_date,
                payment_method,
                amount_paid,
                amount_remaining,
                total_amount,
                payment_id,
                created_at,
                updated_at,
            ) = r
            row = Cols()
            row.id = id_
            row.order_id = order_id
            row.user_id = user_id
            row.user_id_formatted = user_id_fmt
            row.customer_name = customer_name
            row.order_date = order_date
            row.payment_method = payment_method
            row.amount_paid = amount_paid
            row.amount_remaining = amount_remaining
            row.total_amount = total_amount
            row.payment_id = payment_id
            row.created_at = created_at
            row.updated_at = updated_at
            entries = entries_by_payment[id_] if id_ in entries_by_payment else []
            docs.append(_payment__map_to_schema(row, entries))
        return docs

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
        (
            id_,
            order_id,
            user_id,
            user_id_fmt,
            customer_name,
            order_date,
            payment_method,
            amount_paid,
            amount_remaining,
            total_amount,
            payment_id,
            created_at,
            updated_at,
        ) = row
        Cols = type("Cols", (), {})
        r = Cols()
        r.id = id_
        r.order_id = order_id
        r.user_id = user_id
        r.user_id_formatted = user_id_fmt
        r.customer_name = customer_name
        r.order_date = order_date
        r.payment_method = payment_method
        r.amount_paid = amount_paid
        r.amount_remaining = amount_remaining
        r.total_amount = total_amount
        r.payment_id = payment_id
        r.created_at = created_at
        r.updated_at = updated_at
        async with factory() as session:
            entries_by_payment = await self._get_entries_for_payment_ids(session, [pid])
        entries = entries_by_payment[pid] if pid in entries_by_payment else []
        return _payment__map_to_schema(r, entries)

    async def findOne(self, query: Dict) -> Optional[Payment]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

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
        # Since existing is a Dict and update_data is a PaymentInternalUpdate, we merge by accessing update_data fields
        # falling back to existing.
        merged = {
            "order_id": update_data.order_id if update_data.order_id is not None else existing.order_id,
            "user_id": update_data.user_id if update_data.user_id is not None else existing.user_id,
            "user_id_formatted": update_data.user_id_formatted if update_data.user_id_formatted is not None else existing.user_id_formatted,
            "customer_name": update_data.customer_name if update_data.customer_name is not None else existing.customer_name,
            "order_date": update_data.order_date if update_data.order_date is not None else existing.order_date,
            "payment_method": update_data.payment_method if update_data.payment_method is not None else existing.payment_method,
            "amount_paid": update_data.amount_paid if update_data.amount_paid is not None else existing.amount_paid,
            "amount_remaining": update_data.amount_remaining if update_data.amount_remaining is not None else existing.amount_remaining,
            "total_amount": update_data.total_amount if update_data.total_amount is not None else existing.total_amount,
            "payment_id": update_data.payment_id if update_data.payment_id is not None else existing.payment_id,
        }

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
                    "order_id": merged["order_id"],
                    "user_id": merged["user_id"],
                    "user_id_formatted": merged["user_id_formatted"],
                    "customer_name": merged["customer_name"],
                    "order_date": _to_ts(merged["order_date"]),
                    "payment_method": merged["payment_method"],
                    "amount_paid": merged["amount_paid"],
                    "amount_remaining": merged["amount_remaining"],
                    "total_amount": merged["total_amount"],
                    "payment_id": merged["payment_id"],
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
                            "payment_method": entry.payment_method or merged["payment_method"],
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

    async def deleteMany(self, query: Dict) -> Payment:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        return len(await self.findAll(query))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
