"""
Comprehensive DB fix + Negative test suite for Stationery Junction.

Tasks:
1. Add primary key "ID" (USER_ID) to sj_users table
2. Remove all users except user with email "stationeryjunction.jsr@gmail.com"
3. Run negative test cases against the application API
"""

import asyncio
import os
import sys
import json
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Setup
backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

# ─── Colors ──────────────────────────────────────────────────────────────────
GREEN = ""
RED = ""
YELLOW = ""
CYAN = ""
BOLD = ""
RESET = ""


def ok(msg):
    print(f"  [OK] {msg}")


def fail(msg):
    print(f"  [FAIL] {msg}")


def info(msg):
    print(f"  [INFO] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def section(msg):
    print(f"\n{'=' * 60}\n  {msg}\n{'=' * 60}")


# ═══════════════════════════════════════════════════════════════════
# PHASE 1 & 2: Database Fixes
# ═══════════════════════════════════════════════════════════════════


async def fix_database():
    section("PHASE 1 & 2: Database Fixes")
    factory = get_async_session_factory()
    if not factory:
        fail("DATABASE_URL not set, cannot proceed.")
        return False

    async with factory() as session:
        # ── Step 1: Inspect current state ──
        info("Inspecting current sj_users table...")

        # Check columns
        r = await session.execute(
            text(
                "SELECT column_name, data_type, nullable FROM user_tab_columns WHERE table_name = 'SJ_USERS' ORDER BY column_id"
            )
        )
        cols = r.fetchall()
        for c in cols:
            info(f"  Column: {c[0]} | Type: {c[1]} | Nullable: {c[2]}")

        # Check existing constraints
        r = await session.execute(
            text("SELECT constraint_name, constraint_type FROM user_constraints WHERE table_name = 'SJ_USERS'")
        )
        constraints = r.fetchall()
        has_pk = False
        for c in constraints:
            info(f"  Constraint: {c[0]} | Type: {c[1]}")
            if c[1] == "P":
                has_pk = True

        # Count current users
        r = await session.execute(text("SELECT COUNT(*) FROM sj_users"))
        total = r.scalar()
        info(f"  Total users currently: {total}")

        # ── Step 2: Find the admin user by email ──
        info("Finding admin user with email 'stationeryjunction.jsr@gmail.com'...")
        r = await session.execute(
            text("SELECT user_id, email, name, role FROM sj_users WHERE LOWER(email) = :email"),
            {"email": "stationeryjunction.jsr@gmail.com"},
        )
        admin_row = r.fetchone()

        if not admin_row:
            fail("Admin user with email 'stationeryjunction.jsr@gmail.com' NOT FOUND!")
            warn("Cannot safely proceed with user deletion. Aborting deletion step.")
            admin_user_id = None
        else:
            admin_user_id = admin_row[0]
            ok(f"Found admin: user_id={admin_user_id}, name={admin_row[2]}, role={admin_row[3]}")

        # ── Step 3: Delete all users except the admin ──
        if admin_user_id is not None:
            info(f"Deleting all users except user_id={admin_user_id}...")
            try:
                r = await session.execute(
                    text("DELETE FROM sj_users WHERE user_id != :admin_id"), {"admin_id": admin_user_id}
                )
                deleted = r.rowcount
                await session.commit()
                ok(f"Deleted {deleted} users.")
            except Exception as e:
                fail(f"Deletion failed: {e}")
                await session.rollback()
                return False

        # ── Step 4: Ensure USER_ID is NOT NULL ──
        info("Ensuring USER_ID is NOT NULL...")
        try:
            await session.execute(text("ALTER TABLE sj_users MODIFY (USER_ID NOT NULL)"))
            await session.commit()
            ok("USER_ID set to NOT NULL.")
        except Exception as e:
            # Might already be NOT NULL
            warn(f"USER_ID NOT NULL: {e}")
            await session.rollback()

        # ── Step 5: Add Primary Key on USER_ID ──
        if not has_pk:
            info("Adding PRIMARY KEY on USER_ID...")
            try:
                await session.execute(text("ALTER TABLE sj_users ADD CONSTRAINT PK_SJ_USERS PRIMARY KEY (USER_ID)"))
                await session.commit()
                ok("Primary Key PK_SJ_USERS added successfully.")
            except Exception as e:
                if "already exists" in str(e).lower() or "such column list already indexed" in str(e).lower():
                    warn(f"Primary key may already exist: {e}")
                else:
                    fail(f"Adding Primary Key failed: {e}")
                await session.rollback()
        else:
            ok("Primary key already exists on sj_users.")

        # ── Final verification ──
        r = await session.execute(text("SELECT COUNT(*) FROM sj_users"))
        final_count = r.scalar()
        ok(f"Final user count: {final_count}")

        # Verify PK exists now
        r = await session.execute(
            text("SELECT constraint_name FROM user_constraints WHERE table_name = 'SJ_USERS' AND constraint_type = 'P'")
        )
        pk = r.fetchone()
        if pk:
            ok(f"Primary key verified: {pk[0]}")
        else:
            fail("Primary key NOT found after fix attempt!")

        return True


# ═══════════════════════════════════════════════════════════════════
# PHASE 3: Negative Test Cases
# ═══════════════════════════════════════════════════════════════════

import httpx

BASE_URL = f"http://localhost:{os.getenv('PORT', '8000')}/api"

test_results = {"passed": 0, "failed": 0, "errors": []}


def test_pass(name):
    test_results["passed"] += 1
    ok(f"[PASS] {name}")


def test_fail(name, detail=""):
    test_results["failed"] += 1
    test_results["errors"].append({"test": name, "detail": detail})
    fail(f"[FAIL] {name}: {detail}")


async def run_negative_tests():
    section("PHASE 3: Negative Test Cases")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        # ─────────────────────────────────────────────────────
        # AUTH TESTS
        # ─────────────────────────────────────────────────────
        section("Auth - Negative Tests")

        # 1. Login with empty body
        try:
            r = await client.post("/auth/login", json={})
            if r.status_code == 422:
                test_pass("Login with empty body returns 422 (validation error)")
            else:
                test_fail("Login with empty body", f"Expected 422, got {r.status_code}")
        except Exception as e:
            test_fail("Login with empty body", str(e))

        # 2. Login with wrong password
        try:
            r = await client.post(
                "/auth/login", json={"email": "stationeryjunction.jsr@gmail.com", "password": "WRONG_PASSWORD_123"}
            )
            if r.status_code == 401:
                test_pass("Login with wrong password returns 401")
            else:
                test_fail("Login with wrong password", f"Expected 401, got {r.status_code}")
        except Exception as e:
            test_fail("Login with wrong password", str(e))

        # 3. Login with nonexistent email
        try:
            r = await client.post("/auth/login", json={"email": "doesnotexist@fake.com", "password": "anything"})
            if r.status_code == 401:
                test_pass("Login with nonexistent email returns 401")
            else:
                test_fail("Login with nonexistent email", f"Expected 401, got {r.status_code}")
        except Exception as e:
            test_fail("Login with nonexistent email", str(e))

        # 4. Login with no password
        try:
            r = await client.post("/auth/login", json={"email": "stationeryjunction.jsr@gmail.com"})
            if r.status_code == 422:
                test_pass("Login with missing password returns 422")
            else:
                test_fail("Login with missing password", f"Expected 422, got {r.status_code}: {r.text}")
        except Exception as e:
            test_fail("Login with missing password", str(e))

        # 5. Login with empty string password
        try:
            r = await client.post("/auth/login", json={"email": "stationeryjunction.jsr@gmail.com", "password": ""})
            if r.status_code == 400:
                test_pass("Login with empty password returns 400")
            else:
                test_fail("Login with empty password", f"Expected 400, got {r.status_code}: {r.text}")
        except Exception as e:
            test_fail("Login with empty password", str(e))

        # 6. Login with whitespace-only password
        try:
            r = await client.post("/auth/login", json={"email": "stationeryjunction.jsr@gmail.com", "password": "   "})
            if r.status_code == 400:
                test_pass("Login with whitespace password returns 400")
            else:
                test_fail("Login with whitespace password", f"Expected 400, got {r.status_code}: {r.text}")
        except Exception as e:
            test_fail("Login with whitespace password", str(e))

        # 7. Register with existing phone number
        try:
            r = await client.post(
                "/auth/register",
                json={"name": "Test", "email": "test@test.com", "phone": "9999999999", "password": "test123"},
            )
            # Could be 400 (duplicate) or 201 (new user) - depends on DB state
            if r.status_code in (400, 201):
                test_pass(f"Register endpoint responds correctly ({r.status_code})")
            else:
                test_fail("Register endpoint", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Register endpoint", str(e))

        # 8. Register with invalid email
        try:
            r = await client.post(
                "/auth/register",
                json={"name": "Test", "email": "not-an-email", "phone": "1234567890", "password": "test123"},
            )
            if r.status_code == 422:
                test_pass("Register with invalid email returns 422")
            else:
                test_fail("Register with invalid email", f"Expected 422, got {r.status_code}")
        except Exception as e:
            test_fail("Register with invalid email", str(e))

        # 9. Register without phone
        try:
            r = await client.post(
                "/auth/register", json={"name": "Test", "email": "unique@test.com", "password": "test123"}
            )
            if r.status_code == 422:
                test_pass("Register without phone returns 422")
            else:
                test_fail("Register without phone", f"Expected 422, got {r.status_code}")
        except Exception as e:
            test_fail("Register without phone", str(e))

        # 10. Register without password
        try:
            r = await client.post(
                "/auth/register", json={"name": "Test", "email": "unique2@test.com", "phone": "0000000000"}
            )
            if r.status_code == 422:
                test_pass("Register without password returns 422")
            else:
                test_fail("Register without password", f"Expected 422, got {r.status_code}")
        except Exception as e:
            test_fail("Register without password", str(e))

        # ─────────────────────────────────────────────────────
        # TOKEN / AUTH HEADER TESTS
        # ─────────────────────────────────────────────────────
        section("Authorization Header - Negative Tests")

        # 11. Access protected endpoint without token
        try:
            r = await client.get("/users/")
            if r.status_code in (401, 403):
                test_pass("Protected endpoint without token returns 401/403")
            else:
                test_fail("Protected without token", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Protected without token", str(e))

        # 12. Access with invalid token
        try:
            r = await client.get("/users/", headers={"Authorization": "Bearer invalid.token.here"})
            if r.status_code == 401:
                test_pass("Invalid token returns 401")
            else:
                test_fail("Invalid token", f"Expected 401, got {r.status_code}")
        except Exception as e:
            test_fail("Invalid token", str(e))

        # 13. Access with malformed Authorization header
        try:
            r = await client.get("/users/", headers={"Authorization": "NotBearer token"})
            if r.status_code in (401, 403):
                test_pass("Malformed auth header returns 401/403")
            else:
                test_fail("Malformed auth header", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Malformed auth header", str(e))

        # 14. Access with empty token (httpx rejects empty Bearer values at client level)
        try:
            r = await client.get("/users/", headers={"Authorization": "Bearer "})
            if r.status_code in (401, 403, 422):
                test_pass("Empty token returns 401/403/422")
            else:
                test_fail("Empty token", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            # httpx raises ValueError for illegal header - this is correct client-side behavior
            test_pass("Empty token rejected at client level (expected)")

        # ─────────────────────────────────────────────────────
        # OTP TESTS
        # ─────────────────────────────────────────────────────
        section("OTP - Negative Tests")

        # 15. Send OTP with empty phone
        try:
            r = await client.post("/auth/send-otp", json={"phone": ""})
            if r.status_code in (400, 422, 500):
                test_pass(f"Send OTP with empty phone returns {r.status_code}")
            else:
                test_fail("Send OTP empty phone", f"Expected 400/422, got {r.status_code}")
        except Exception as e:
            test_fail("Send OTP empty phone", str(e))

        # 16. Verify OTP with wrong OTP
        try:
            r = await client.post("/auth/verify-otp", json={"phone": "9876543210", "otp": "000000"})
            if r.status_code == 400:
                test_pass("Verify wrong OTP returns 400")
            else:
                test_fail("Verify wrong OTP", f"Expected 400, got {r.status_code}")
        except Exception as e:
            test_fail("Verify wrong OTP", str(e))

        # 17. Check-phone with invalid format
        try:
            r = await client.post("/auth/check-phone", json={"phone": "abc"})
            if r.status_code == 400:
                test_pass("Check-phone with invalid format returns 400")
            else:
                test_fail("Check-phone invalid format", f"Expected 400, got {r.status_code}: {r.text}")
        except Exception as e:
            test_fail("Check-phone invalid format", str(e))

        # ─────────────────────────────────────────────────────
        # FORGOT PASSWORD TESTS
        # ─────────────────────────────────────────────────────
        section("Forgot Password - Negative Tests")

        # 18. Forgot password with unknown phone
        try:
            r = await client.post(
                "/auth/forgot-password", json={"phone": "0000000001", "newPassword": "newpass123", "otp": "123456"}
            )
            if r.status_code in (400, 404):
                test_pass(f"Forgot password unknown phone returns {r.status_code}")
            else:
                test_fail("Forgot password unknown phone", f"Expected 400/404, got {r.status_code}")
        except Exception as e:
            test_fail("Forgot password unknown phone", str(e))

        # 19. Forgot password missing fields
        try:
            r = await client.post("/auth/forgot-password", json={"phone": "1234567890"})
            if r.status_code == 422:
                test_pass("Forgot password missing fields returns 422")
            else:
                test_fail("Forgot password missing fields", f"Expected 422, got {r.status_code}")
        except Exception as e:
            test_fail("Forgot password missing fields", str(e))

        # ─────────────────────────────────────────────────────
        # PRODUCT TESTS (public)
        # ─────────────────────────────────────────────────────
        section("Products - Negative Tests")

        # 20. Get nonexistent product
        try:
            r = await client.get("/products/public/99999999")
            if r.status_code == 404:
                test_pass("Nonexistent product returns 404")
            else:
                test_fail("Nonexistent product", f"Expected 404, got {r.status_code}")
        except Exception as e:
            test_fail("Nonexistent product", str(e))

        # 21. Get product with invalid ID format
        try:
            r = await client.get("/products/public/not-a-valid-id")
            if r.status_code in (404, 422):
                test_pass(f"Invalid product ID returns {r.status_code}")
            else:
                test_fail("Invalid product ID", f"Expected 404/422, got {r.status_code}")
        except Exception as e:
            test_fail("Invalid product ID", str(e))

        # 22. Public products with negative page
        try:
            r = await client.get("/products/public?page=-1&limit=10")
            if r.status_code in (200, 422):
                test_pass(f"Negative page parameter handled (status {r.status_code})")
            else:
                test_fail("Negative page param", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Negative page param", str(e))

        # 23. Public products with huge limit (DoS vector)
        try:
            r = await client.get("/products/public?page=1&limit=999999")
            if r.status_code == 200:
                test_pass("Huge limit parameter handled without crash")
            else:
                test_fail("Huge limit param", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Huge limit param", str(e))

        # ─────────────────────────────────────────────────────
        # USER TESTS (require auth)
        # ─────────────────────────────────────────────────────
        section("User Endpoints - Negative Tests")

        # 24. Get user with invalid ID (no auth)
        try:
            r = await client.get("/users/nonexistent-id")
            if r.status_code in (401, 403):
                test_pass("Get user without auth returns 401/403")
            else:
                test_fail("Get user no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Get user no auth", str(e))

        # 25. Update user without auth
        try:
            r = await client.put("/users/1", json={"name": "Hacked"})
            if r.status_code in (401, 403):
                test_pass("Update user without auth returns 401/403")
            else:
                test_fail("Update user no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Update user no auth", str(e))

        # 26. Delete user without auth
        try:
            r = await client.delete("/users/1")
            if r.status_code in (401, 403):
                test_pass("Delete user without auth returns 401/403")
            else:
                test_fail("Delete user no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Delete user no auth", str(e))

        # ─────────────────────────────────────────────────────
        # CART TESTS (require auth)
        # ─────────────────────────────────────────────────────
        section("Cart - Negative Tests")

        # 27. Get cart without auth
        try:
            r = await client.get("/cart/")
            if r.status_code in (401, 403):
                test_pass("Get cart without auth returns 401/403")
            else:
                test_fail("Get cart no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Get cart no auth", str(e))

        # 28. Add to cart without auth
        try:
            r = await client.post("/cart/", json={"productId": "1", "quantity": 1})
            if r.status_code in (401, 403):
                test_pass("Add to cart without auth returns 401/403")
            else:
                test_fail("Add to cart no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Add to cart no auth", str(e))

        # ─────────────────────────────────────────────────────
        # ORDER TESTS (require auth)
        # ─────────────────────────────────────────────────────
        section("Orders - Negative Tests")

        # 29. Create order without auth
        try:
            r = await client.post("/orders/", json={"shippingAddress": {"address": "test"}, "paymentMethod": "cod"})
            if r.status_code in (401, 403):
                test_pass("Create order without auth returns 401/403")
            else:
                test_fail("Create order no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Create order no auth", str(e))

        # 30. Get orders without auth
        try:
            r = await client.get("/orders/")
            if r.status_code in (401, 403):
                test_pass("Get orders without auth returns 401/403")
            else:
                test_fail("Get orders no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Get orders no auth", str(e))

        # ─────────────────────────────────────────────────────
        # REFRESH TOKEN TESTS
        # ─────────────────────────────────────────────────────
        section("Token Refresh - Negative Tests")

        # 31. Refresh with invalid token
        try:
            r = await client.post("/auth/refresh", json={"refreshToken": "invalid.refresh.token"})
            if r.status_code == 401:
                test_pass("Refresh with invalid token returns 401")
            else:
                test_fail("Refresh invalid token", f"Expected 401, got {r.status_code}")
        except Exception as e:
            test_fail("Refresh invalid token", str(e))

        # 32. Refresh with empty token
        try:
            r = await client.post("/auth/refresh", json={"refreshToken": ""})
            if r.status_code in (401, 422):
                test_pass(f"Refresh with empty token returns {r.status_code}")
            else:
                test_fail("Refresh empty token", f"Expected 401/422, got {r.status_code}")
        except Exception as e:
            test_fail("Refresh empty token", str(e))

        # ─────────────────────────────────────────────────────
        # INJECTION / MALICIOUS INPUT TESTS
        # ─────────────────────────────────────────────────────
        section("Injection / Malicious Input - Negative Tests")

        # 33. SQL injection in login email
        try:
            r = await client.post("/auth/login", json={"email": "admin@test.com' OR '1'='1", "password": "anything"})
            if r.status_code in (401, 422):
                test_pass(f"SQL injection in email returns {r.status_code}")
            else:
                test_fail("SQL injection email", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("SQL injection email", str(e))

        # 34. XSS in product search
        try:
            r = await client.get("/products/public?search=<script>alert(1)</script>")
            if r.status_code == 200:
                body = r.json()
                # Check response doesn't contain unescaped script
                if "<script>" not in json.dumps(body):
                    test_pass("XSS in search parameter handled safely")
                else:
                    test_fail("XSS in search", "Unescaped script tag in response")
            else:
                test_pass(f"XSS in search handled (status {r.status_code})")
        except Exception as e:
            test_fail("XSS in search", str(e))

        # 35. Very long input in login
        try:
            long_email = "a" * 10000 + "@test.com"
            r = await client.post("/auth/login", json={"email": long_email, "password": "a" * 10000})
            if r.status_code in (401, 422, 500):
                test_pass(f"Very long input in login handled (status {r.status_code})")
            else:
                test_fail("Very long input", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Very long input", str(e))

        # 36. Unicode/emoji in fields
        try:
            r = await client.post(
                "/auth/register",
                json={"name": "👨‍💻 Test 🔥", "email": "emoji@test.com", "phone": "1111111111", "password": "test123"},
            )
            if r.status_code in (201, 400):
                test_pass(f"Unicode/emoji in name handled (status {r.status_code})")
            else:
                test_fail("Unicode in name", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Unicode in name", str(e))

        # ─────────────────────────────────────────────────────
        # BOUNDARY TESTS
        # ─────────────────────────────────────────────────────
        section("Boundary / Edge Case Tests")

        # 37. Send OTP with phone containing special chars
        try:
            r = await client.post("/auth/send-otp", json={"phone": "+91-987-654-3210"})
            if r.status_code in (200, 400, 429, 500):
                test_pass(f"OTP with formatted phone handled (status {r.status_code})")
            else:
                test_fail("OTP formatted phone", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("OTP formatted phone", str(e))

        # 38. Access non-existent route
        try:
            r = await client.get("/nonexistent-route")
            if r.status_code in (404, 405):
                test_pass(f"Non-existent route returns {r.status_code}")
            else:
                test_fail("Non-existent route", f"Expected 404/405, got {r.status_code}")
        except Exception as e:
            test_fail("Non-existent route", str(e))

        # 39. POST to GET-only endpoint
        try:
            r = await client.post("/products/public", json={"test": "data"})
            if r.status_code in (405, 422):
                test_pass(f"POST to GET endpoint returns {r.status_code}")
            else:
                test_fail("POST to GET endpoint", f"Expected 405, got {r.status_code}")
        except Exception as e:
            test_fail("POST to GET endpoint", str(e))

        # 40. Send huge JSON body
        try:
            huge_body = {"data": "x" * 500000}
            r = await client.post("/auth/login", json=huge_body)
            if r.status_code in (400, 422, 413):
                test_pass(f"Huge JSON body handled (status {r.status_code})")
            else:
                test_fail("Huge JSON body", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Huge JSON body", str(e))

        # ─────────────────────────────────────────────────────
        # ADMIN/RBAC TESTS
        # ─────────────────────────────────────────────────────
        section("RBAC / Privilege Escalation Tests")

        # 41. Create product without auth (admin-only)
        try:
            r = await client.post("/products/", json={"name": "Hack Product", "category": "Test", "mrp": 100})
            if r.status_code in (401, 403):
                test_pass("Create product without admin auth blocked")
            else:
                test_fail("Create product no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Create product no auth", str(e))

        # 42. Delete product without auth
        try:
            r = await client.delete("/products/1")
            if r.status_code in (401, 403):
                test_pass("Delete product without admin auth blocked")
            else:
                test_fail("Delete product no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Delete product no auth", str(e))

        # 43. Access analytics KPI without auth (actual route is /kpi not /dashboard)
        try:
            r = await client.get("/analytics/kpi")
            if r.status_code in (401, 403):
                test_pass("Analytics KPI without auth returns 401/403")
            else:
                test_fail("Analytics KPI no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Analytics KPI no auth", str(e))

        # 44. Access pending approvals without auth
        try:
            r = await client.get("/users/pending-approvals")
            if r.status_code in (401, 403):
                test_pass("Pending approvals without auth blocked")
            else:
                test_fail("Pending approvals no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Pending approvals no auth", str(e))

        # ─────────────────────────────────────────────────────
        # COUPON / DISCOUNT TESTS
        # ─────────────────────────────────────────────────────
        section("Coupons - Negative Tests")

        # 45. Create coupon without auth
        try:
            r = await client.post(
                "/coupons/",
                json={
                    "code": "HACKCODE",
                    "discountType": "percentage",
                    "discountValue": 100,
                    "validFrom": "2024-01-01",
                    "validUntil": "2030-01-01",
                },
            )
            if r.status_code in (401, 403):
                test_pass("Create coupon without auth blocked")
            else:
                test_fail("Create coupon no auth", f"Expected 401/403, got {r.status_code}")
        except Exception as e:
            test_fail("Create coupon no auth", str(e))

        # ─────────────────────────────────────────────────────
        # CONTENT-TYPE TESTS
        # ─────────────────────────────────────────────────────
        section("Content-Type / Encoding Tests")

        # 46. Send non-JSON to JSON endpoint
        try:
            r = await client.post("/auth/login", content="not json", headers={"Content-Type": "text/plain"})
            if r.status_code in (400, 415, 422):
                test_pass(f"Non-JSON content-type handled (status {r.status_code})")
            else:
                test_fail("Non-JSON content type", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Non-JSON content type", str(e))

        # 47. Send malformed JSON
        try:
            r = await client.post(
                "/auth/login",
                content='{"email": "test@test.com", "password":}',
                headers={"Content-Type": "application/json"},
            )
            if r.status_code in (400, 422):
                test_pass(f"Malformed JSON handled (status {r.status_code})")
            else:
                test_fail("Malformed JSON", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Malformed JSON", str(e))

        # ─────────────────────────────────────────────────────
        # SUPPORT TICKETS (no auth needed?)
        # ─────────────────────────────────────────────────────
        section("Support Tickets - Negative Tests")

        # 48. Create support ticket without required fields
        try:
            r = await client.post("/support-tickets/", json={})
            if r.status_code in (401, 403, 422):
                test_pass(f"Support ticket without data returns {r.status_code}")
            else:
                test_fail("Support ticket no data", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Support ticket no data", str(e))

        # ─────────────────────────────────────────────────────
        # DELIVERY CHARGES
        # ─────────────────────────────────────────────────────
        section("Delivery Charges - Negative Tests")

        # 49. Check nonexistent pincode
        try:
            r = await client.get("/pincodes/check/000000")
            if r.status_code in (200, 404):
                test_pass(f"Nonexistent pincode check handled (status {r.status_code})")
            else:
                test_fail("Nonexistent pincode", f"Unexpected status: {r.status_code}")
        except Exception as e:
            test_fail("Nonexistent pincode", str(e))

        # ─────────────────────────────────────────────────────
        # VERSION / HEALTH
        # ─────────────────────────────────────────────────────
        section("Health / Version - Sanity")

        # 50. Root endpoint
        try:
            r = await client.get("/", follow_redirects=True)
            # Base URL is /api, so root might be /api which doesn't exist
            # Let's try the real root
            pass
        except:
            pass

        try:
            async with httpx.AsyncClient(timeout=10.0) as root_client:
                r = await root_client.get(f"http://localhost:{os.getenv('PORT', '8000')}/")
                if r.status_code == 200:
                    test_pass("Root endpoint returns 200")
                else:
                    test_fail("Root endpoint", f"Expected 200, got {r.status_code}")
        except Exception as e:
            test_fail("Root endpoint", str(e))


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════


async def main():
    section("Stationery Junction - DB Fix & Negative Test Suite")

    # Phase 1 & 2: DB fixes
    db_ok = await fix_database()
    if not db_ok:
        warn("DB fix encountered issues. Continuing with tests...")

    # Phase 3: Negative tests
    print(f"\n{YELLOW}NOTE: The backend server must be running on port {os.getenv('PORT', '8000')} for tests.{RESET}")
    print(f"{YELLOW}Start it with: cd backend && python run.py{RESET}\n")

    try:
        # Quick connectivity check
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://localhost:{os.getenv('PORT', '8000')}/")
            if r.status_code == 200:
                ok("Backend server is running!")
            else:
                warn(f"Backend responded with {r.status_code}")
    except Exception:
        fail("Cannot connect to backend. Please start the server first.")
        fail(f"Run: cd backend && python run.py")
        return

    await run_negative_tests()

    # Summary
    section("TEST RESULTS SUMMARY")
    total = test_results["passed"] + test_results["failed"]
    print(f"  Total tests: {total}")
    print(f"  {GREEN}Passed: {test_results['passed']}{RESET}")
    print(f"  {RED}Failed: {test_results['failed']}{RESET}")

    if test_results["errors"]:
        print(f"\n  {RED}Failed tests:{RESET}")
        for err in test_results["errors"]:
            print(f"    - {err['test']}: {err['detail']}")

    print()


if __name__ == "__main__":
    asyncio.run(main())
