# Schema Q&A

## What is **payload** in the tracking table?

**payload** is a catch-all JSON column. The tracking DAO maps known fields (type, userId, sessionId, searchTerm, productIds, etc.) to fixed or `product_ids` columns. **Any other field** sent by the app (e.g. `cartItems`, `pageViews`, `isReturning`, `quantity`) is merged into **payload**. So one event might have `payload = {"cartItems": [...], "cartValue": 100}` and another `{"pageViews": 1, "isReturning": true}`. It stays as one JSON column so we don’t add a new DB column for every optional tracking field.

---

## What is **external_id** in all tables?

**external_id** is a unique, non-sequential identifier (e.g. 32-char hex from `secrets.token_hex(16)`). It is used to:

1. **Refetch the row after INSERT** – Oracle IDENTITY doesn’t always return the new `id` in the same round-trip, so we insert with `external_id`, then `SELECT id FROM table WHERE external_id = :eid` to get the new PK.
2. **Stable public ID** – If you expose an ID in APIs or URLs, you can use `external_id` instead of the numeric `id`, so PKs are not guessable or enumerable.

So: **id** = internal PK (number); **external_id** = stable, unique token for the same row.

---

## What are **meta** and **device** in activities? (Device is fixed → separate columns)

- **device** – Comes from `app.utils.device.parse_device()` and has **fixed keys**: `userAgent`, `os`, `osVersion`, `deviceType`, `appVersion`, `deviceModel`, `locale`, `ip`. So it can be stored as **separate columns** instead of one JSON column.
- **meta** – Passed as a dict from the client and can be arbitrary (extra context per action). So **meta** stays as a single JSON column; only **device** is normalized into columns in the schema/DAOs.

---

## What is **data** in notifications?

**data** is a type-specific payload attached to each notification:

- **new_order** – `orderId`, `orderNumber`, `amount`, `userId`, `createdAt`
- **new_payment** – `paymentId`, `paymentIdFormatted`, `orderId`, `amount`, `paymentMethod`, `createdAt`
- **new_return** – `returnId`, `orderId`
- (Other types like **low_stock** can have different keys.)

So the **shape varies by `type`**. Keeping **data** as one JSON column avoids a wide table with many nullable columns or multiple tables per notification type. If you prefer, we can add a few fixed columns (e.g. `order_id`, `payment_id`, `return_id`) for filtering and keep the rest in **data**.

---

## Payment entries → separate rows (done)

**Payment entries** are stored as **separate rows** in **sj_payment_entries** (FK to **sj_payments**). One row per entry: entry_id, amount, payment_method, paid_at, image, notes, verified, created_at. **OraclePaymentDAO** reads/writes `sj_payments` and `sj_payment_entries` and exposes the same API (payment dict with `paymentEntries` array) to the payment repository.

---

## Why is **description** in support tickets JSON?

It was switched to JSON when all former “variable” columns were moved from CLOB to JSON. **description** is plain long text (ticket body), not structured data. It should be **VARCHAR2(4000)** or **CLOB**, not JSON. The schema and typed-doc config are being updated so **description** is a normal scalar column.
