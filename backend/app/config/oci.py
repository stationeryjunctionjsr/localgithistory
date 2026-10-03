"""
OCI Object Storage configuration. Bucket is private; use PAR/signed URLs for read access.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Bucket: sj-prod-assets (private). No public access.
OCI_BUCKET_NAME = os.environ.get("OCI_BUCKET_NAME", "sj-prod-assets")
OCI_NAMESPACE = os.environ.get("OCI_NAMESPACE", "axiekhoevpfn")
OCI_REGION = os.environ.get("OCI_REGION", "ap-hyderabad-1")

# OCI API Key Authentication
OCI_USER_OCID = os.environ.get("OCI_USER_OCID")
OCI_TENANCY_OCID = os.environ.get("OCI_TENANCY_OCID")
OCI_FINGERPRINT = os.environ.get("OCI_FINGERPRINT")

# SEC-8: Private key can be supplied as a file path (OCI_PRIVATE_KEY_FILE) or
# inline in an env var (OCI_PRIVATE_KEY).  File takes precedence so that
# production deployments can mount a secret file instead of embedding a
# multi-line PEM key in the environment.
_key_file_path = os.environ.get("OCI_PRIVATE_KEY_FILE", "").strip()
if _key_file_path:
    try:
        with open(_key_file_path, "r", encoding="utf-8") as _f:
            OCI_PRIVATE_KEY: str | None = _f.read()
    except OSError as _e:
        logger.warning("OCI_PRIVATE_KEY_FILE is set but could not be read (%s): %s", _key_file_path, _e)
        OCI_PRIVATE_KEY = None
else:
    OCI_PRIVATE_KEY = os.environ.get("OCI_PRIVATE_KEY")

# PAR validity for read URLs (seconds). Short = lower risk; 1 hour is a reasonable default.
OCI_PAR_EXPIRY_SECONDS = int(os.environ.get("OCI_PAR_EXPIRY_SECONDS", "3600"))


def use_oci_storage() -> bool:
    """True if OCI Object Storage should be used for uploads and media."""
    if not (OCI_BUCKET_NAME and OCI_NAMESPACE and OCI_REGION):
        return False
    if not OCI_USER_OCID:
        return False
    if not OCI_PRIVATE_KEY:
        return False
    try:
        from cryptography.hazmat.primitives import serialization

        key_content = OCI_PRIVATE_KEY.strip().strip('"').strip("'").strip()
        if "\\n" in key_content:
            key_content = key_content.replace("\\n", "\n")
        serialization.load_pem_private_key(key_content.encode("utf-8"), password=None)
        return True
    except Exception:
        logger.warning(
            "OCI private key is set but failed to parse as a valid PEM key; OCI storage disabled.",
            exc_info=True,
        )
        return False

