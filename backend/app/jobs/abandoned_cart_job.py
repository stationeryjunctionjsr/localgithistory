"""
Abandoned Cart Recovery Job
===========================
Runs every 30 minutes via APScheduler.

Data source:
  - sj_tracking            — one row per cart_abandonment event
                             (event_type='cart_abandonment', user_id=external varchar)
  - sj_tracking_cart_items — child rows with product_id + quantity + price
                             (FK → sj_tracking.id)

Sends (per channel, in order):
  1. Email  — via existing EmailService (SMTP)
  2. Push   — via existing PushNotificationService (web-push / Expo)
  [WhatsApp] — future; stub comment included below.

Deduplication:
  sj_abandoned_cart_reminders table (created by the migration at the bottom
  of this file). One row per (user_id, reminder); prevents re-firing within
  REMINDER_COOLDOWN_H hours.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.config.database import get_async_session_factory
from app.services.email_service import email_service
from app.services.push_notification_service import push_notification_service
from app.utils.logger import logger

# ── Tunables ──────────────────────────────────────────────────────────────────
ABANDON_AFTER_MINUTES = 30       # event must be at least this old
ABANDON_MAX_HOURS     = 72       # ignore events older than this (stale)
REMINDER_COOLDOWN_H   = 24       # one reminder per user per this many hours
FRONTEND_BASE_URL     = "https://stationeryjunction.in"
# ─────────────────────────────────────────────────────────────────────────────

# DDL — run once (idempotent)
MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS sj_abandoned_cart_reminders (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_external_id VARCHAR(64)  NOT NULL,
    tracking_id     INT          NOT NULL,
    sent_at         DATETIME     NOT NULL,
    channels        VARCHAR(128) NOT NULL,
    INDEX idx_acr_user (user_external_id),
    INDEX idx_acr_sent (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


async def _ensure_table():
    """Create sj_abandoned_cart_reminders if it doesn't exist yet."""
    from sqlalchemy import text

    factory = get_async_session_factory()
    if not factory:
        return
    async with factory() as session:
        await session.execute(text(MIGRATION_SQL))
        await session.commit()


async def _get_abandoned_events(session, cutoff_min: datetime, cutoff_max: datetime):
    """
    Return rows with all info needed to send a recovery message.

    Selects the *latest* cart_abandonment event per user within the idle window,
    joined with their email/name and the cart items stored in sj_tracking_cart_items.

    sj_tracking.user_id  is the *external* string ID of the user.
    sj_users.external_id matches it.
    """
    from sqlalchemy import text

    sql = text("""
        SELECT
            t.id                      AS tracking_id,
            t.user_id                 AS user_external_id,
            t.created_at              AS abandoned_at,
            t.cart_value,
            u.id                      AS user_pk,
            u.email,
            COALESCE(u.name, u.email) AS customer_name,
            GROUP_CONCAT(
                DISTINCT COALESCE(p.name, tci.product_id)
                ORDER BY tci.id
                SEPARATOR '|'
            ) AS product_names
        FROM sj_tracking t
        JOIN sj_users u
            ON u.external_id = t.user_id
        LEFT JOIN sj_tracking_cart_items tci
            ON tci.tracking_id = t.id
        LEFT JOIN sj_products p
            ON p.external_id = tci.product_id
        WHERE
            t.event_type = 'cart_abandonment'
            AND t.user_id IS NOT NULL
            AND t.created_at  < :cutoff_min
            AND t.created_at  > :cutoff_max
            AND u.email IS NOT NULL
            AND u.email != ''
            /* user has NOT placed an order after this abandonment event */
            AND NOT EXISTS (
                SELECT 1 FROM sj_orders o
                WHERE o.user_id = u.id
                  AND o.created_at >= t.created_at
            )
        GROUP BY
            t.id, t.user_id, t.created_at, t.cart_value,
            u.id, u.email, u.name
        HAVING COUNT(tci.id) > 0
        ORDER BY t.created_at DESC
    """)

    result = await session.execute(sql, {
        "cutoff_min": cutoff_min,
        "cutoff_max": cutoff_max,
    })
    return result.fetchall()


async def _already_notified(session, user_external_id: str, cooldown_cutoff: datetime) -> bool:
    """True if a reminder was already sent for this user within the cooldown window."""
    from sqlalchemy import text

    result = await session.execute(
        text("""
            SELECT 1 FROM sj_abandoned_cart_reminders
            WHERE user_external_id = :uid
              AND sent_at >= :cutoff
            LIMIT 1
        """),
        {"uid": user_external_id, "cutoff": cooldown_cutoff},
    )
    return result.fetchone() is not None


async def _record_notification(
    session, user_external_id: str, tracking_id: int, channels: str
):
    """Insert a deduplication record after a successful send."""
    from sqlalchemy import text

    await session.execute(
        text("""
            INSERT INTO sj_abandoned_cart_reminders
                (user_external_id, tracking_id, sent_at, channels)
            VALUES
                (:uid, :tid, :now, :channels)
        """),
        {
            "uid":      user_external_id,
            "tid":      tracking_id,
            "now":      datetime.now(timezone.utc).replace(tzinfo=None),
            "channels": channels,
        },
    )
    await session.commit()


def _build_email_html(
    customer_name: str, product_names: list[str], cart_url: str
) -> tuple[str, str]:
    """Return (subject, html_body) for the abandoned cart email."""
    first_name = customer_name.split()[0] if customer_name else "there"

    items_html = "".join(
        f"<li style='margin-bottom:4px;color:#374151;'>{name}</li>"
        for name in product_names[:5]
    )
    if len(product_names) > 5:
        items_html += (
            f"<li style='color:#6b7280;'>… and {len(product_names) - 5} more item(s)</li>"
        )

    subject = "You left something behind 🛒 — Stationery Junction"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                padding:24px;border:1px solid #e0e0e0;border-radius:8px;">

      <div style="text-align:center;border-bottom:2px solid #6d28d9;
                  padding-bottom:12px;margin-bottom:20px;">
        <h1 style="color:#6d28d9;margin:0;font-size:22px;">Stationery Junction</h1>
        <p style="color:#6b7280;margin:4px 0 0;font-size:13px;">Your cart is waiting for you</p>
      </div>

      <p style="margin:0 0 12px;">Hi <strong>{first_name}</strong>,</p>
      <p style="color:#374151;margin:0 0 16px;">
        Looks like you left some great items in your cart.
        They&#39;re still available — complete your purchase before they sell out!
      </p>

      <div style="background:#faf5ff;border:1px solid #e9d5ff;border-radius:6px;
                  padding:16px;margin:0 0 20px;">
        <p style="font-weight:700;margin:0 0 8px;color:#5b21b6;">Items in your cart:</p>
        <ul style="margin:0;padding-left:20px;">
          {items_html}
        </ul>
      </div>

      <div style="text-align:center;margin:24px 0;">
        <a href="{cart_url}"
           style="background:linear-gradient(135deg,#7c3aed,#6d28d9);
                  color:#ffffff;padding:14px 32px;border-radius:8px;
                  text-decoration:none;font-weight:700;font-size:16px;
                  display:inline-block;">
          Complete My Order →
        </a>
      </div>

      <p style="font-size:13px;color:#6b7280;margin:0;">
        Need help? Visit our
        <a href="{FRONTEND_BASE_URL}/support" style="color:#6d28d9;">support page</a>.
      </p>

      <div style="border-top:1px solid #e0e0e0;padding-top:12px;font-size:12px;
                  color:#9ca3af;text-align:center;margin-top:20px;">
        <p style="margin:0;">© 2026 Stationery Junction. All rights reserved.</p>
        <p style="margin:4px 0 0;">
          You received this because you have items saved in your cart.
        </p>
      </div>
    </div>
    """
    return subject, html_body


async def run_abandoned_cart_job():
    """
    Main entry-point called by APScheduler every 30 minutes.

    Strategy:
      1. Ensure the dedup table exists (idempotent DDL).
      2. Query sj_tracking for recent cart_abandonment events whose users
         haven't ordered since and haven't been reminded recently.
      3. For each candidate: send email + push, record the dedup row.
    """
    logger.info("[AbandonedCart] Job started at %s", datetime.now(timezone.utc).isoformat())

    factory = get_async_session_factory()
    if not factory:
        logger.warning("[AbandonedCart] MySQL not configured — skipping.")
        return

    await _ensure_table()

    now        = datetime.now(timezone.utc)
    cutoff_min = (now - timedelta(minutes=ABANDON_AFTER_MINUTES)).replace(tzinfo=None)
    cutoff_max = (now - timedelta(hours=ABANDON_MAX_HOURS)).replace(tzinfo=None)
    cooldown_cutoff = (now - timedelta(hours=REMINDER_COOLDOWN_H)).replace(tzinfo=None)

    try:
        async with factory() as session:
            rows = await _get_abandoned_events(session, cutoff_min, cutoff_max)
    except Exception as exc:
        logger.error("[AbandonedCart] Failed to query abandoned events: %s", exc, exc_info=True)
        return

    logger.info("[AbandonedCart] Found %d candidate event(s).", len(rows))

    # De-duplicate by user at the Python level too — keep only the latest
    # event per user if multiple abandonment events exist in the window.
    seen_users: set[str] = set()

    for row in rows:
        user_ext_id  = row.user_external_id
        user_pk      = row.user_pk
        email        = row.email
        name         = row.customer_name or email
        tracking_id  = row.tracking_id
        raw_products = row.product_names or ""
        product_names = [p.strip() for p in raw_products.split("|") if p.strip()]

        if not email or not product_names:
            continue
        if user_ext_id in seen_users:
            continue   # already processed a newer event for this user
        seen_users.add(user_ext_id)

        # ── Cooldown check ────────────────────────────────────────────────────
        async with factory() as session:
            if await _already_notified(session, user_ext_id, cooldown_cutoff):
                logger.debug(
                    "[AbandonedCart] Skipping user %s — notified within cooldown.", user_ext_id
                )
                continue

        cart_url = f"{FRONTEND_BASE_URL}/customer/cart"
        channels_sent: list[str] = []
        push_message = (
            product_names[0]
            + (f" + {len(product_names) - 1} more" if len(product_names) > 1 else "")
            + " — complete your order now!"
        )

        # ── 1. Email ──────────────────────────────────────────────────────────
        try:
            subject, html_body = _build_email_html(name, product_names, cart_url)
            plain_body = (
                f"Hi {name},\n\n"
                "You left items in your cart at Stationery Junction.\n"
                f"Complete your order here: {cart_url}\n\n"
                f"Items: {', '.join(product_names[:5])}\n\n"
                "— The Stationery Junction Team"
            )
            sent = await asyncio.to_thread(
                email_service.send_email, email, subject, plain_body, html_body
            )
            if sent:
                channels_sent.append("email")
                logger.info(
                    "[AbandonedCart] Email sent → user %s (%s)", user_ext_id, email
                )
            else:
                logger.warning(
                    "[AbandonedCart] Email returned False for user %s", user_ext_id
                )
        except Exception as exc:
            logger.error(
                "[AbandonedCart] Email failed for user %s: %s", user_ext_id, exc, exc_info=True
            )

        # ── 2. In-app notification + Push ─────────────────────────────────────
        try:
            from app.utils.notify import notify_user
            await notify_user(
                user_id    = str(user_ext_id),
                notif_type = "abandoned_cart",
                title      = "Your cart is waiting 🛒",
                message    = push_message,
                link       = cart_url,
                metadata   = {"status": "reminder_sent"},
            )
            channels_sent.append("push")
            logger.info("[AbandonedCart] In-app + push sent → user %s", user_ext_id)
        except Exception as exc:
            logger.error(
                "[AbandonedCart] In-app/push failed for user %s: %s", user_ext_id, exc, exc_info=True
            )

        # ── WhatsApp (future) ─────────────────────────────────────────────────
        # Uncomment and implement when WA Business API is configured:
        # try:
        #     await whatsapp_service.send_cart_reminder(
        #         phone=user_phone, name=name,
        #         product_names=product_names, cart_url=cart_url
        #     )
        #     channels_sent.append("whatsapp")
        # except Exception as exc:
        #     logger.error("[AbandonedCart] WA failed for user %s: %s", user_ext_id, exc)

        # ── Record dedup entry ────────────────────────────────────────────────
        if channels_sent:
            async with factory() as session:
                await _record_notification(
                    session,
                    user_external_id=user_ext_id,
                    tracking_id=tracking_id,
                    channels=",".join(channels_sent),
                )
            logger.info(
                "[AbandonedCart] Reminder recorded for user %s via [%s]",
                user_ext_id, ", ".join(channels_sent),
            )
        else:
            logger.warning(
                "[AbandonedCart] No channel succeeded for user %s (tracking_id=%d)",
                user_ext_id, tracking_id,
            )

    logger.info("[AbandonedCart] Job finished.")
