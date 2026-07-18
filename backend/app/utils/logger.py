import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.utils.error_handler import EmailLogHandler

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# ContextVar that middleware sets per-request; defaults to "-" when outside a request
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class CorrelationIdFilter(logging.Filter):
    """Injects the current request_id into every log record automatically."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


# Configure logging
def setup_logging():
    logger = logging.getLogger("stationery_junction")
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if already configured
    if logger.handlers:
        return logger

    from pythonjsonlogger import jsonlogger

    # Formatter: Structured JSON logging — includes request_id for correlation
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(module)s %(request_id)s %(message)s",
        json_ensure_ascii=False,
    )

    correlation_filter = CorrelationIdFilter()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    logger.addHandler(console_handler)

    # File Handler (Rotating: 5MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)
    logger.addHandler(file_handler)

    # Email Handler (Critical Alerts)
    email_handler = EmailLogHandler()
    email_handler.setFormatter(formatter)
    email_handler.addFilter(correlation_filter)
    logger.addHandler(email_handler)

    return logger


# Initialize logger
logger = setup_logging()
