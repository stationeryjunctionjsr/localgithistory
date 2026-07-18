import hashlib
import logging
from datetime import datetime, timedelta

import psutil

try:
    from sqlalchemy import text

    from app.config.database import use_oracle
except ImportError:
    def use_oracle():
        return False

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
            # Create a hash of the message (ignoring unique parts like user IDs)
            # We use the first 100 characters + level
            msg_key = f"{record.levelno}:{record.msg[:100]}"
            error_hash = hashlib.md5(msg_key.encode()).hexdigest()

            now = datetime.now()
            error_data = notified_errors_data.get(error_hash)

            if not error_data:
                error_data = {"last_sent": None, "users": set(), "created_at": now}
                notified_errors_data[error_hash] = error_data

            # Track affected users if available in message
            current_user = "anonymous"
            if "user " in message:
                try:
                    current_user = message.split("user ")[1].split("\n")[0].strip()
                except Exception:
                    current_user = "anonymous"

            error_data["users"].add(current_user)

            # --- Evaluation & Throttling ---
            last_sent = error_data["last_sent"]
            user_count = len(error_data["users"])
            is_resource_alert = "System Resource Alert" in message

            # 1. Check Threshold (5 unique users, except resources)
            if not is_resource_alert and user_count < 5:
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
                f"Affected Users (since last alert): {user_count}\n\n"
                f"Message:\n{message}"
            )

            # Send alert
            from app.services.email_service import email_service
            if email_service.send_error_alert(subject, body):
                error_data["last_sent"] = now
                # IMPORTANT: Reset users count for the next batch after sending
                error_data["users"].clear()

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
            resource_logger.critical(
                "System Resource Alert: High CPU Usage (>80%%). Current: %.1f%%", cpu_p
            )

        # Memory Usage
        mem = psutil.virtual_memory()
        if mem.percent > 80:
            resource_logger.critical(
                "System Resource Alert: High Memory Usage (>80%%). Current: %.1f%%", mem.percent
            )

        # Disk Usage — check the filesystem where the app data/logs live
        import shutil
        disk = shutil.disk_usage("/")
        disk_pct = disk.used / disk.total * 100
        if disk_pct > 85:
            disk_free_gb = disk.free / (1024 ** 3)
            resource_logger.critical(
                "System Resource Alert: High Disk Usage (>85%%). Used: %.1f%%, Free: %.2f GB",
                disk_pct,
                disk_free_gb,
            )

    except Exception as e:
        logging.getLogger("stationery_junction").error("Error checking system resources: %s", str(e), exc_info=True)


async def check_db_usage(db_session):
    """Oracle specific DB usage check."""
    if not use_oracle():
        return

    try:
        # Query to check tablespace usage
        query = text("""
            SELECT tablespace_name, used_percent
            FROM dba_tablespace_usage_metrics
            WHERE used_percent > 80
        """)
        result = await db_session.execute(query)
        for row in result:
            logging.getLogger("stationery_junction").critical(
                f"DB Resource Alert: Tablespace '{row.tablespace_name}' is >80% full. Current: {row.used_percent}%"
            )

        # Check session count
        query_sessions = text("""
            SELECT (SELECT count(*) FROM v$session) /
                   (SELECT value FROM v$parameter WHERE name = 'sessions') * 100 as pct
            FROM dual
        """)
        res_sessions = await db_session.execute(query_sessions)
        pct = res_sessions.scalar()
        if pct and pct > 80:
            logging.getLogger("stationery_junction").critical(
                f"DB Resource Alert: Session Limit is >80%. Current: {pct:.1f}%"
            )

    except Exception as e:
        logging.getLogger("stationery_junction").warning(f"Failed to check DB usage: {e}")
