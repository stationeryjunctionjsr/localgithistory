import asyncio
from app.config.database import get_async_session_factory
from sqlalchemy import text


async def create_table():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS sj_email_otp_send_log (id int AUTO_INCREMENT PRIMARY KEY, email varchar(255), sent_at datetime, KEY ix_sj_email_otp_send_log_email (email), KEY ix_sj_email_otp_send_log_sent (sent_at))"
            )
        )
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS sj_email_otps (id int AUTO_INCREMENT PRIMARY KEY, email varchar(255), device_key varchar(255), otp_code varchar(10), verify_attempts int, created_at datetime, expires_at datetime, last_sent_at datetime, KEY ix_sj_email_otps_email (email), KEY ix_sj_email_otps_expires (expires_at))"
            )
        )
        await session.commit()
    print("Tables created")


asyncio.run(create_table())
