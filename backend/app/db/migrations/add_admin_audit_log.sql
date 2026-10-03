-- ANA-5: Admin Audit Log
-- Tracks high-risk mutations performed by admin / super_admin users.
-- Table is append-only (no updates, no deletes via application code).

CREATE TABLE IF NOT EXISTS sj_admin_audit_log (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_id      VARCHAR(64)     NOT NULL COMMENT 'User ID of the admin who performed the action',
    actor_role    VARCHAR(32)     NOT NULL COMMENT 'Role at time of action: super_admin, wholesaler, etc.',
    action        VARCHAR(64)     NOT NULL COMMENT 'Verb: approve, reject, delete, role_change, deactivate, …',
    entity_type   VARCHAR(64)     NOT NULL COMMENT 'Logical entity: user, product, coupon, order, …',
    entity_id     VARCHAR(64)         NULL COMMENT 'PK of the affected row (may be NULL for bulk ops)',
    change_summary JSON                NULL COMMENT 'Optional JSON diff — PII-free summary only',
    ip_address    VARCHAR(45)         NULL COMMENT 'Client IP (IPv4 or IPv6)',
    created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    INDEX idx_actor     (actor_id, created_at),
    INDEX idx_entity    (entity_type, entity_id, created_at),
    INDEX idx_action    (action, created_at),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Append-only admin action audit trail (ANA-5)';
