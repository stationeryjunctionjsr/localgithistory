# Schema Q&A (part 2)

## What is **payload** in customer segments and events?

- **Customer segments:** Each segment has a fixed column `type` (e.g. `retail` / `business`). The **payload** JSON holds the rest: `name`, `userIds` (list of user IDs in the segment), `filters` (e.g. `{ "behavior": "churned" }`), `isActive`, `isSystem`, `lastRefreshedAt`. So the shape varies per segment; the job writes refreshed `userIds` and `lastRefreshedAt` into it.

- **Events:** Used for analytics. The table has `event_type` (column) and **payload** (JSON). The payload is the variable part of the event: e.g. `userId`, `sessionId`, `page`, `properties`, or whatever the client sends. So each event is one row; the body of the event is in **payload**.

---

## What are **retail** and **business** in referral settings?

Referral settings have **two segments**: retail (customers) and business (wholesalers). Each has its own config object:

- **retail** = `{ "segment": "retail", "discountType": "percentage"|"fixed", "discountValue": number, "isActive": bool }`
- **business** = same shape for the business segment

So **retail** and **business** are two JSON columns, one per segment, each holding a `ReferralSegmentSetting` (discount type, value, active flag). They are not arrays; they are single objects per segment.

---

## Saved for later: separate rows per user (not JSON)

Saved-for-later is now **one row per saved item** (per user + product), not one row per user with an `items` JSON array. Table shape: `user_id`, `product_id`, `saved_at` (and ids/timestamps). The DAO still exposes the same API to the app: `findOne({ user: user_id })` returns a virtual doc `{ user, items: [ { productId, savedAt }, ... ] }` built from those rows; create/update translate to insert/delete of rows.

---

## What are **keys** and **subscription** in device subscriptions?

Used for **Web Push**:

- **subscription:** The full Web Push subscription object from the browser (e.g. `PushSubscription`): at least `endpoint` (URL) and often `expirationTime`, etc. Stored as-is so the backend can send push messages to that endpoint.

- **keys:** The encryption key part of the subscription: `{ "p256dh": "...", "auth": "..." }`. The push service uses these to encrypt payloads. Often the client sends `subscription` and the app stores `subscription` and `subscription.keys` separately; both are needed to send web push. So **keys** = `p256dh` + `auth`; **subscription** = full object (endpoint + keys). Both stay as JSON because they are opaque client-specific blobs.

---

## 1. Will the recommendation algo work fine with JSON columns?

**Yes.** The recommendation logic runs in the **app layer** (Python). It uses the same storage interface as the rest of the app: `get_storage("orders")`, `get_storage("activities")`, etc. Those return **already-parsed** Python dicts/lists. The DAOs read JSON columns from Oracle, run `json_loads`, and put the result into the dict. So the recommendation code never sees raw JSON; it only sees normal Python structures. It does not need to query inside JSON in SQL. So JSON columns do not affect the recommendation algo.

---

## 2. Whenever a value in a JSON column is modified, is the complete value rewritten?

**In our current code: yes.** We do **read full doc → merge in app → write full doc**. So when we UPDATE a row and set a JSON column, we send the **entire new** JSON value (the full object or array). The database replaces the whole column value.

Oracle can do **partial** JSON updates (e.g. `JSON_TRANSFORM`) so only a path is updated, but we are not using that. If you need to avoid rewriting large JSON for small changes, we could add partial-update support later (e.g. `JSON_TRANSFORM` in SQL or a dedicated method in the DAO).

---

## What was meant by “payment entries passed as JSON”?

**At the API/repository layer** the app still **passes and receives** payment data with a **`paymentEntries` array** (a list of objects: amount, paymentMethod, paidAt, image, notes, verified, etc.). So in Python you have something like:

```python
payment = {
  "orderId": "...",
  "totalAmount": 100,
  "paymentEntries": [
    { "entryId": 1, "amount": 50, "paymentMethod": "upi", "paidAt": "...", ... },
    { "entryId": 2, "amount": 50, "paymentMethod": "cod", ... }
  ]
}
```

So in memory and in the API it’s still “list of entries” (you can think of it as “passed as JSON” when sent over HTTP). **In the database** we no longer store that list in one JSON column. We store **one row per entry** in **sj_payment_entries** (with `payment_id` FK to the payment). **OraclePaymentDAO** does the mapping: when **reading**, it loads payment rows and entry rows and **assembles** the `paymentEntries` array; when **creating/updating**, it **writes** each element of `paymentEntries` as a row in `sj_payment_entries`. So: **API still uses a list of entries; DB stores them as separate rows.**

---

## Reports and analytics: can they use JSON columns?

**Yes.** You can use JSON columns in reports and analytics in two ways:

1. **App layer (current)**  
   Reports and analytics use the same storage layer (`get_storage(...)`). DAOs read JSON columns, parse them in Python, and return dicts/lists. So any report that uses the repositories or DAOs already “uses” JSON data; it just sees normal Python structures. No change needed.

2. **SQL / Oracle JSON functions**  
   If you want to report or aggregate **directly in SQL** using data inside a JSON column, Oracle supports that:
   - **JSON_VALUE(column, '$.path')** – one scalar (e.g. for filters or GROUP BY).
   - **JSON_QUERY(column, '$.path')** – a JSON fragment.
   - **JSON_TABLE(column, '$.path' COLUMNS (...))** – turn JSON array elements into rows for JOINs/aggregation.

   Example (conceptual): count events by a key inside `payload`:
   ```sql
   SELECT JSON_VALUE(payload, '$.userId') AS user_id, COUNT(*) 
   FROM sj_events 
   WHERE event_type = 'page_view' 
   GROUP BY JSON_VALUE(payload, '$.userId');
   ```

   So reporting and analytics **can** use JSON columns both via the app (already) and via SQL (Oracle JSON functions) when you need DB-level reporting.
