# UPI Configuration
import logging
import os

logger = logging.getLogger(__name__)

UPI_ID = os.getenv("UPI_ID", "stationeryjunction@paytm")
UPI_QR_CODE_URL = os.getenv("UPI_QR_CODE_URL", "/public/upi-qr-code.png")

# Warn in production if UPI credentials are not set
_env = os.getenv("APP_ENV", "development")
if _env == "production":
    if not os.getenv("UPI_ID"):
        logger.warning("UPI_ID env variable is not set in production; using placeholder value.")
    if not os.getenv("UPI_QR_CODE_URL"):
        logger.warning("UPI_QR_CODE_URL env variable is not set in production; using placeholder path.")
