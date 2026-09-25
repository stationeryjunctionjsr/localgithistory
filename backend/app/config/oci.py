"""
OCI Object Storage configuration. Bucket is private; use PAR/signed URLs for read access.
"""
import logging

import os

# Bucket: sj-prod-assets (private). No public access.
OCI_BUCKET_NAME = os.environ["OCI_BUCKET_NAME"] if "OCI_BUCKET_NAME" in os.environ else "sj-prod-assets"
OCI_NAMESPACE = os.environ["OCI_NAMESPACE"] if "OCI_NAMESPACE" in os.environ else "axiekhoevpfn"
OCI_REGION = os.environ["OCI_REGION"] if "OCI_REGION" in os.environ else "ap-hyderabad-1"

# OCI API Key Authentication
OCI_USER_OCID = os.environ["OCI_USER_OCID"] if "OCI_USER_OCID" in os.environ else None
OCI_TENANCY_OCID = os.environ["OCI_TENANCY_OCID"] if "OCI_TENANCY_OCID" in os.environ else None
OCI_FINGERPRINT = os.environ["OCI_FINGERPRINT"] if "OCI_FINGERPRINT" in os.environ else None
OCI_PRIVATE_KEY = os.environ["OCI_PRIVATE_KEY"] if "OCI_PRIVATE_KEY" in os.environ else None

# PAR validity for read URLs (seconds). Short = lower risk; 1 hour is a reasonable default.
OCI_PAR_EXPIRY_SECONDS = int(os.environ["OCI_PAR_EXPIRY_SECONDS"] if "OCI_PAR_EXPIRY_SECONDS" in os.environ else "3600")

logger = logging.getLogger(__name__)


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
        logger.warning("OCI private key is set but failed to parse as a valid PEM key; OCI storage disabled.", exc_info=True)
        return False

