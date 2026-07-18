# MySQL migration – what’s needed

Your backend currently uses **JSON file storage** (no SQL database). Data lives in `app/data/*.json` and is accessed via `FileStorage` in `app/utils/file_storage.py`. Migrating to MySQL means adding a MySQL-backed storage layer and (optionally) moving existing data into MySQL.

---

## What I need from you

### 1. MySQL connection details (or env vars)

- **Host** (e.g. `localhost` or your DB server)
- **Port** (default `3306`)
- **Database name** (e.g. `stationery_junction`)
- **User** and **Password**

Preferred: provide these via environment variables (e.g. in `.env`) so nothing is committed:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`

If you already use a different naming (e.g. `DATABASE_URL`), tell me the names and I’ll use those.

### 2. MySQL server

- Confirm MySQL (or MariaDB / compatible server) is installed and running, or that you’ll use a cloud instance (e.g. AWS RDS, PlanetScale).
- If you want, I can add a small script or `docker-compose` snippet to run MySQL locally.

### 3. Migration scope

Choose one (or both) and I’ll align the plan:

- **A) Code-only:** Implement MySQL storage and make the app use it. You handle creating the DB and (if needed) importing data later.
- **B) Code + data migration:** Implement MySQL storage **and** a one-off script that reads current `app/data/*.json` and inserts into MySQL so existing users, products, orders, etc. are preserved.

### 4. Preferences (optional)

- **ORM:** Prefer **SQLAlchemy 2 (async)** or **raw SQL** (e.g. `aiomysql`)?  
  Recommendation: SQLAlchemy 2 async for clearer schema and easier maintenance.
- **IDs:** Keep current string `_id` (e.g. hex) in MySQL, or switch to auto-increment integers for some tables?  
  Recommendation: keep `_id` as primary key for minimal code change and easier migration.

---

## What the migration will do (once the above is clear)

1. **Schema design**  
   Define MySQL tables that match your current JSON “collections”, including:
   - users, products, orders (with order items), carts, wishlists, coupons, banners, brands, categories  
   - deliveryCharges, deliveryChargeDefaults, orderFeedback, contacts, supportTickets  
   - tracking, savedForLater, payments, featureFlags, notifications, categoryTags  
   - pushNotifications, deviceSubscriptions, sessions, activities, promoStrips, collections, searchTags, coachMarks  

2. **Storage abstraction**  
   - Introduce a small **storage interface** (e.g. `findAll`, `findById`, `findOne`, `create`, `update`, `delete`) that matches current `FileStorage` usage.
   - Implement **MySQL storage** that satisfies this interface (and handles JSON columns where you have nested objects, e.g. order items, address).

3. **Wiring**  
   - Add config (from env) for MySQL.
   - Use the MySQL implementation when `USE_MYSQL=true` (or similar), and keep file storage as fallback or for local dev if you want.

4. **Data migration (if you chose B)**  
   - One-off script that:
     - Reads each `app/data/<collection>.json`
     - Maps documents to the new tables (including nested structures stored as JSON columns or related tables where appropriate)
     - Inserts into MySQL (with conflict handling if you want idempotency).

5. **Edge cases**  
   - Fix or align any repo that uses methods not on current `FileStorage` (e.g. `write`, `find_all`, `find_by_id`) so they use the common interface or the new MySQL implementation.

---

## Quick reply template

You can reply with something like:

- **MySQL:** “Use env vars: MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD” (or your names).
- **Server:** “Local MySQL” / “AWS RDS” / “PlanetScale” / “Not set up yet”.
- **Scope:** “Code only” or “Code + data migration”.
- **ORM:** “SQLAlchemy async” or “Raw SQL”.
- **IDs:** “Keep string _id” or “Use integers where it makes sense”.

Once you provide this, the next step is to implement the MySQL schema and storage layer and then the migration script if you chose B.
