-- ============================================================
-- Migration: Add UNIQUE constraints on sj_users.email and sj_users.phone
-- Purpose:   Enforce data-integrity uniqueness at the DB layer to prevent
--            duplicate accounts that can bypass application-level checks.
-- Replaces:  The non-unique ix_sj_users_email / ix_sj_users_phone indexes.
-- Prereq:    Resolve any existing duplicate email/phone rows BEFORE running.
-- ── 1. Find duplicate emails (fix these before proceeding) ───────────────────
-- SELECT email, COUNT(*) c FROM sj_users WHERE email IS NOT NULL GROUP BY email HAVING c > 1;
-- ── 2. Find duplicate phones (fix these before proceeding) ───────────────────
-- SELECT phone, COUNT(*) c FROM sj_users WHERE phone IS NOT NULL GROUP BY phone HAVING c > 1;
-- ── 3. Drop the old non-unique indexes ───────────────────────────────────────
ALTER TABLE sj_users DROP INDEX ix_sj_users_email;
ALTER TABLE sj_users DROP INDEX ix_sj_users_phone;
-- ── 4. Create UNIQUE indexes ─────────────────────────────────────────────────
-- NULL values are allowed in a UNIQUE index in MySQL 8: multiple rows with
-- NULL email/phone will NOT conflict, which is correct for guest accounts.
CREATE UNIQUE INDEX uq_sj_users_email ON sj_users (email);
CREATE UNIQUE INDEX uq_sj_users_phone ON sj_users (phone);
