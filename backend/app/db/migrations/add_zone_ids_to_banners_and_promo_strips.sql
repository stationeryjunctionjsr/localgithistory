-- Migration: Add zone_ids column to banners and promo strips for zone-based filtering
-- zone_ids stores a JSON array of zone external_ids.
-- NULL means the banner/strip applies to ALL zones (backward-compatible default).

ALTER TABLE sj_banners
    ADD COLUMN zone_ids TEXT DEFAULT NULL
    COMMENT 'JSON array of zone external_ids; NULL = all zones';

ALTER TABLE sj_promo_strips
    ADD COLUMN zone_ids TEXT DEFAULT NULL
    COMMENT 'JSON array of zone external_ids; NULL = all zones';
