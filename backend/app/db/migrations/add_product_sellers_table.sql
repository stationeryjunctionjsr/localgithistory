-- Migration: Add sj_product_sellers junction table
-- Purpose: Enable DB-level filtering of products by seller, fixing in-memory pincode
--          filtering that causes broken pagination totalCount and under-full pages.
-- Run once. Safe to re-run (uses IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS sj_product_sellers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    product_id      VARCHAR(64)  NOT NULL COMMENT 'Matches sj_products.external_id',
    seller_id       VARCHAR(64)  NOT NULL COMMENT 'Matches sj_users.external_id',
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    request_status  VARCHAR(32)  NOT NULL DEFAULT 'approved',
    stock           INT          NOT NULL DEFAULT 0,
    variant_ids     JSON,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX ix_ps_seller_active   (seller_id, is_active, request_status),
    INDEX ix_ps_product_id      (product_id),
    INDEX ix_ps_seller_id       (seller_id),
    UNIQUE KEY uq_ps_product_seller (product_id, seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backfill: Populate from existing product sellers data in sj_products.details JSON
INSERT IGNORE INTO sj_product_sellers (product_id, seller_id, is_active, request_status, stock)
SELECT
    p.external_id                                                    AS product_id,
    JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.sellerId'))               AS seller_id,
    CASE WHEN JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.isActive')) = 'true' THEN 1 ELSE 0 END AS is_active,
    COALESCE(JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.requestStatus')), 'approved') AS request_status,
    COALESCE(CAST(JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.stock')) AS SIGNED), 0) AS stock
FROM sj_products p
JOIN JSON_TABLE(
    JSON_EXTRACT(p.details, '$.sellers'),
    '$[*]' COLUMNS (seller JSON PATH '$')
) AS s
WHERE JSON_EXTRACT(p.details, '$.sellers') IS NOT NULL
  AND JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.sellerId')) IS NOT NULL
  AND JSON_UNQUOTE(JSON_EXTRACT(s.seller, '$.sellerId')) != 'null';
