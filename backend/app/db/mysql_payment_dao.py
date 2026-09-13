"""
MySQL DAO for payments: sj_payments (header) + sj_payment_entries (child rows).
Assembles paymentEntries from child table; create/update write entries as separate rows.
"""

import secrets
from datetime import datetime
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
    if hasattr(val, "isoformat"):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


def _entry_row_to_dict(entry_id, amount, payment_method, paid_at, image, notes, verified, created_at) -> Dict:
    return {
        "entryId": entry_id,
        "amount": float(amount) if amount is not None else 0,
        "paymentMethod": payment_method,
        "paidAt": paid_at.isoformat() if hasattr(paid_at, "isoformat") and paid_at else None,
        "image": image,
        "notes": notes,
        "verified": bool(verified) if verified is not None else False,
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") and created_at else None,
    }


def _payment_row_to_dict(r, entries: List[Dict]) -> Dict:
    doc = {
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
    }
    return doc


class MySQLPaymentDAO:
    @property
    def PAYMENTS_TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_payments{suffix}"

    @property
    def ENTRIES_TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_payment_entries{suffix}"

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
            by_payment[pid].append(_entry_row_to_dict(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
        return by_payment

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            if query.get("orderId"):
                where_clauses.append("order_id = :order_id")
                params["order_id"] = query["orderId"]
            if query.get("userId"):
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
            entries = entries_by_payment.get(id_, [])
            docs.append(_payment_row_to_dict(row, entries))
        return docs

    async def findById(self, id: str) -> Optional[Dict]:
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
        entries = entries_by_payment.get(pid, [])
        return _payment_row_to_dict(r, entries)

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def create(self, data: PaymentInternalCreate) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        payment_entries = data.paymentEntries or []
        params = {
            "external_id": external_id,
            "order_id": data.orderId,
            "user_id": data.userId,
            "user_id_formatted": data.userIdFormatted,
            "customer_name": data.customerName,
            "order_date": _to_ts(data.orderDate) or now,
            "payment_method": data.paymentMethod,
            "amount_paid": data.amountPaid,
            "amount_remaining": data.amountRemaining,
            "total_amount": data.totalAmount,
            "payment_id": data.paymentId,
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
                    entry_id = (entry.entryId if entry.entryId is not None else idx + 1)
                    amount = (entry.amount if entry.amount is not None else 0)
                    method = entry.paymentMethod or data.paymentMethod
                    paid_at = _to_ts(entry.paidAt) or now
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

    async def update(self, id: str, update_data: PaymentInternalUpdate) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        # Since existing is a Dict and update_data is a PaymentInternalUpdate, we merge by accessing update_data fields
        # falling back to existing.
        merged = {}
        for k in ["orderId", "userId", "userIdFormatted", "customerName", "orderDate", "paymentMethod", "amountPaid", "amountRemaining", "totalAmount", "paymentId"]:
            val = getattr(update_data, k, None)
            if val is None:
                val = existing.get(k)
            merged[k] = val

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
                    "order_id": merged["orderId"],
                    "user_id": merged["userId"],
                    "user_id_formatted": merged["userIdFormatted"],
                    "customer_name": merged["customerName"],
                    "order_date": _to_ts(merged["orderDate"]),
                    "payment_method": merged["paymentMethod"],
                    "amount_paid": merged["amountPaid"],
                    "amount_remaining": merged["amountRemaining"],
                    "total_amount": merged["totalAmount"],
                    "payment_id": merged["paymentId"],
                    "updated_at": now,
                    "id": pid,
                },
            )
            await session.commit()
            if update_data.paymentEntries is not None:
                await session.execute(text(f"DELETE FROM {self.ENTRIES_TABLE} WHERE payment_id = :id"), {"id": pid})
                await session.commit()
                for idx, entry in enumerate(update_data.paymentEntries):
                    entry_id = (entry.entryId if entry.entryId is not None else idx + 1)
                    paid_at = _to_ts(entry.paidAt) or now
                    await session.execute(
                        text(
                            f"INSERT INTO {self.ENTRIES_TABLE} (payment_id, entry_id, amount, payment_method, paid_at, image, notes, verified, created_at) "
                            f"VALUES (:payment_id, :entry_id, :amount, :payment_method, :paid_at, :image, :notes, :verified, :created_at)"
                        ),
                        {
                            "payment_id": pid,
                            "entry_id": entry_id,
                            "amount": (entry.amount if entry.amount is not None else 0),
                            "payment_method": entry.paymentMethod or merged["paymentMethod"],
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

    async def deleteMany(self, query: Dict) -> Dict:
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
