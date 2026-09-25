"""
Centralised application settings using Pydantic BaseSettings.

All environment variables are declared here with types and defaults.
Import the singleton `settings` anywhere instead of calling os.getenv() directly.

Usage:
    from app.config.settings import settings
    # Access settings like: settings.environment, settings.database_url
    # Never log or print secret fields (jwt_secret_key, smtp_password, etc.)
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    port: int = 8000
    environment: str = "development"

    # ── Security ──────────────────────────────────────────────────────────────
    jwt_secret_key: str = ""
    jwt_refresh_secret_key: str = ""
    allowed_origins: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = ""  # Oracle connection string; empty = use JSON file storage
    mongodb_uri: str = ""

    # ── OCI Object Storage ────────────────────────────────────────────────────
    oci_bucket_name: str = ""
    oci_namespace: str = ""
    oci_region: str = ""
    oci_user_ocid: str = ""
    oci_tenancy_ocid: str = ""
    oci_fingerprint: str = ""
    oci_private_key: str = ""
    oci_par_expiry_seconds: int = 3600

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # ── External APIs ─────────────────────────────────────────────────────────
    google_maps_api_key: str = ""
    google_place_id: str = ""

    # ── Maintenance / scheduled upgrade ───────────────────────────────────────
    maintenance_mode: bool = False

    # ── Observability ─────────────────────────────────────────────────────────
    slow_request_threshold_ms: float = 500.0
    sentry_dsn: str = ""  # Leave empty to disable Sentry entirely

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # silently ignore unknown env vars


settings = Settings()

# ── Startup secret validation ─────────────────────────────────────────────────
# Fail fast if JWT keys are still the example placeholders or are too short.
# This prevents the server from booting with a forgeable signing key.
_PLACEHOLDER_FRAGMENTS = ("generate_a_secure", "generate_another", "changeme", "secret_here", "your_secret")
_MIN_KEY_LENGTH = 32  # 32 bytes hex-encoded = 64 chars; reject anything shorter


def _is_weak_key(key: str) -> bool:
    if not key or len(key) < _MIN_KEY_LENGTH:
        return True
    key_lower = key.lower()
    return any(frag in key_lower for frag in _PLACEHOLDER_FRAGMENTS)


_non_dev_envs = {"production", "uat", "staging"}
if settings.environment.lower() in _non_dev_envs:
    if _is_weak_key(settings.jwt_secret_key):
        raise RuntimeError(
            f"[SECURITY] JWT_SECRET_KEY is missing or is a placeholder in "
            f"ENVIRONMENT={settings.environment!r}. "
            "Set a cryptographically random 64-byte hex key before starting the server."
        )
    if _is_weak_key(settings.jwt_refresh_secret_key):
        raise RuntimeError(
            f"[SECURITY] JWT_REFRESH_SECRET_KEY is missing or is a placeholder in "
            f"ENVIRONMENT={settings.environment!r}. "
            "Set a cryptographically random 64-byte hex key before starting the server."
        )
