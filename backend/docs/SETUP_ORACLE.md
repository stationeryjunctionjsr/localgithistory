# What You Have To Do – Oracle Setup

All Oracle tables use the **sj_** prefix (e.g. **sj_users**, **sj_orders**). Follow these steps to use Oracle instead of JSON files.

---

## Step 1: Create the tables in Oracle

1. Open your Oracle database (e.g. SQL Developer, SQL\*Plus, or the Autonomous DB SQL worksheet).
2. Log in as your **application user** (not ADMIN).
3. Run the schema script:  
   **`backend/scripts/schema_oracle.sql`**  
   This creates all **sj_*** tables (sj_users, sj_products, sj_orders, etc.), indexes, and foreign keys.

---

## Step 2: Set your connection in the app

1. In the **backend** folder, copy `.env.example` to `.env` (if you don’t have `.env` yet).
2. In `.env`, set **DATABASE_URL** to your Oracle connection string, for example:
   - `oracle+oracledb://MYUSER:MYPASSWORD@hostname:1521/?service_name=MYSERVICE`
   - For Oracle Autonomous Database, use the connection string from the cloud console (and wallet path if required).

When **DATABASE_URL** is set, the app uses Oracle. When it is not set, the app keeps using the JSON files in **app/data/**.

---

## Step 3: Load your existing data into Oracle (one-time)

1. Make sure **DATABASE_URL** is set in `.env`.
2. From the **backend** folder, run:
   ```bash
   python scripts/migrate_json_to_oracle.py
   ```
   This reads **app/data/*.json** and inserts into the **sj_*** tables (e.g. users → sj_users, activities → sj_activities).

---

## Step 4: Run the app

From the **backend** folder:

```bash
uvicorn app.main:app --reload
```

- If **DATABASE_URL** is set: the app uses Oracle (sj_* tables).
- If **DATABASE_URL** is not set: the app uses JSON files as before.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Run **scripts/schema_oracle.sql** in Oracle (as your app user). |
| 2 | Set **DATABASE_URL** in **backend/.env**. |
| 3 | Run **python scripts/migrate_json_to_oracle.py** once to copy JSON data into Oracle. |
| 4 | Start the app; it will use Oracle when **DATABASE_URL** is set. |

All table names use the **sj_** prefix (e.g. **sj_users**, **sj_orders**, **sj_products**).
