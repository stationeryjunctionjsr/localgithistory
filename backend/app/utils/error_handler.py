import hashlib
import logging
from datetime import datetime, timedelta

import psutil

from sqlalchemy import text


# Global state for throttling (in-memory)
# Format: { error_hash: { last_sent: datetime, users: set(), created_at: datetime } }
notified_errors_data = {}


class EmailLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setLevel(logging.ERROR)

    def emit(self, record):
        try:
            # Only handle ERROR and CRITICAL
            if record.levelno < logging.ERROR:
                return

            message = self.format(record)
            # Create a hash of the message (ignoring unique parts like user IDs).
            # SEC-7: Use SHA-256 instead of MD5 for consistency — this is for
            # bucketing only (not crypto), but SHA-256 is preferred by convention.
            msg_key = f"{record.levelno}:{record.msg[:100]}"
            error_hash = hashlib.sha256(msg_key.encode()).hexdigest()

            now = datetime.now()
            error_data = notified_errors_data[error_hash] if error_hash in notified_errors_data else None

            if not error_data:
                error_data = {"last_sent": None, "users": set(), "created_at": now, "occurrences": 0}
                notified_errors_data[error_hash] = error_data

            # Track affected users if available in message
            current_user = "anonymous"
            if "user " in message:
                try:
                    current_user = message.split("user ")[1].split("\n")[0].strip()
                except Exception:
                    logger.debug("Could not extract user from error message; defaulting to anonymous.", exc_info=True)
                    current_user = "anonymous"

            error_data["users"].add(current_user)
            error_data["occurrences"] = error_data.get("occurrences", 0) + 1

            # --- Evaluation & Throttling ---
            last_sent = error_data["last_sent"]
            user_count = len(error_data["users"])
            occurrence_count = error_data["occurrences"]
            is_resource_alert = "System Resource Alert" in message

            # ANA-4: Threshold is per-worker.  With up to 4 Uvicorn workers each
            # tracking state independently, we lower the per-worker occurrence
            # threshold from 20 → 5 so that ~20 total occurrences across workers
            # still triggers an alert (same logical sensitivity as before).
            if not is_resource_alert and user_count < 5 and occurrence_count < 5:
                return

            # 2. Check Throttling (once per 6 hours)
            if last_sent and (now - last_sent) < timedelta(hours=6):
                return

            # --- If we pass both, Send Email ---
            short_desc = record.msg[:50] + ("..." if len(record.msg) > 50 else "")
            subject = f"MAJOR FRONTEND: {short_desc}"
            if is_resource_alert:
                subject = f"RESOURCES: {short_desc}"

            body = (
                f"Level: {record.levelname}\n"
                f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Module: {record.module}\n"
                f"Occurrences (since last alert): {occurrence_count}\n"
                f"Affected Users (since last alert): {user_count}\n\n"
                f"Message:\n{message}"
            )

            # Send alert
            from app.services.email_service import email_service

            if email_service.send_error_alert(subject, body):
                error_data["last_sent"] = now
                # IMPORTANT: Reset users and occurrence count for the next batch after sending
                error_data["users"].clear()
                error_data["occurrences"] = 0

        except Exception as e:
            # Fallback to console if everything fails
            logging.getLogger("stationery_junction").error("Failed to emit log to email: %s", str(e), exc_info=True)


def check_system_resources():
    """Checks CPU, memory, and disk usage. Logs CRITICAL if any metric exceeds 80%."""
    resource_logger = logging.getLogger("stationery_junction")
    try:
        # CPU Usage
        cpu_p = psutil.cpu_percent(interval=1)
        if cpu_p > 80:
            resource_logger.critical("System Resource Alert: High CPU Usage (>80%%). Current: %.1f%%", cpu_p)

        # Memory Usage
        mem = psutil.virtual_memory()
        if mem.percent > 80:
            resource_logger.critical("System Resource Alert: High Memory Usage (>80%%). Current: %.1f%%", mem.percent)

        # Disk Usage — check the filesystem where the app data/logs live
        import shutil

        disk = shutil.disk_usage("/")
        disk_pct = disk.used / disk.total * 100
        if disk_pct > 85:
            disk_free_gb = disk.free / (1024**3)
            resource_logger.critical(
                "System Resource Alert: High Disk Usage (>85%%). Used: %.1f%%, Free: %.2f GB",
                disk_pct,
                disk_free_gb,
            )

    except Exception as e:
        logging.getLogger("stationery_junction").error("Error checking system resources: %s", str(e), exc_info=True)


async def check_db_usage(db_session) -> None:
    """ANA-7: Check MySQL connection-pool utilisation and log a warning if it exceeds 80%.

    The previous Oracle tablespace implementation has been replaced with a MySQL
    INFORMATION_SCHEMA query against the global `Threads_connected` and
    `max_connections` status variables.
    """
    resource_logger = logging.getLogger("stationery_junction")
    try:
        result = await db_session.execute(
            text(
                """
                SELECT
                    (SELECT VARIABLE_VALUE FROM performance_schema.global_status
                     WHERE VARIABLE_NAME = 'Threads_connected') AS connected,
                    (SELECT VARIABLE_VALUE FROM performance_schema.global_variables
                     WHERE VARIABLE_NAME = 'max_connections')    AS max_conn
                """
            )
        )
        row = result.fetchone()
        if row and row.max_conn:
            connected = int(row.connected or 0)
            max_conn = int(row.max_conn)
            pct = (connected / max_conn) * 100 if max_conn else 0
            if pct > 80:
                resource_logger.critical(
                    "System Resource Alert: MySQL connection pool >80%% utilised. "
                    "Connected: %d / %d (%.1f%%)",
                    connected,
                    max_conn,
                    pct,
                )
    except Exception as e:
        logging.getLogger("stationery_junction").warning("Failed to check DB usage: %s", e, exc_info=True)
