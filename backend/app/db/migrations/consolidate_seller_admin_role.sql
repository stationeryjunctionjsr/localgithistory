-- Migration: Consolidate seller_admin role into seller
-- Reason: seller_admin and seller were treated identically in the application
--         authorization layer (is_seller_admin(), require_seller_admin(),
--         require_super_admin_or_seller()). The SELLER_ADMIN enum value has been
--         removed from UserRole. All seller users now carry role = 'seller'.
-- This migration:
--   1. Promotes any user with role = 'seller_admin' to role = 'seller'
--   2. Promotes any user with is_seller_admin = 1 but a non-seller role
--      (e.g. customer, wholesaler) to role = 'seller'
--   3. Clears the is_seller_admin flag to 0 for all users now on role = 'seller'
--      (the flag is no longer the source of truth — role is)
-- Safe to run multiple times (idempotent via WHERE conditions).
-- ──────────────────────────────────────────────────────────────────────────────

-- Step 1: Promote role = 'seller_admin' → 'seller'
UPDATE sj_users
SET role = 'seller', updated_at = NOW()
WHERE role = 'seller_admin';

-- Step 2: Promote any user flagged as is_seller_admin = 1 but not yet role = 'seller'
--         (e.g. customers or wholesalers who were granted seller access via the flag)
UPDATE sj_users
SET role = 'seller', updated_at = NOW()
WHERE is_seller_admin = 1
  AND role != 'seller';

-- Step 3: Clear the is_seller_admin flag for all seller-role users
--         Role is now the single source of truth.
UPDATE sj_users
SET is_seller_admin = 0, updated_at = NOW()
WHERE role = 'seller'
  AND is_seller_admin = 1;
