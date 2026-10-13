import asyncio
from datetime import datetime
from typing import List, Optional

from app.models.daos_flat import (
    ProductNotificationsInternal,
    ProductNotificationsInternalCreate,
    ProductNotificationsInternalUpdate,
)
from app.db.storage_factory import get_storage
from app.config.settings import settings
from app.services.email_service import email_service
from app.utils.logger import logger


class ProductNotificationRepository:
    def __init__(self) -> None:
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage("productNotifications")
        return self._storage

    async def ensure_table_exists(self) -> None:
        """No-op: Schema is managed via MySQL migrations."""
        return

    async def find_active_by_product_and_email(
        self, product_id: str, email: str
    ) -> Optional[ProductNotificationsInternal]:
        rows = await self.storage.findAll(
            product_id=str(product_id), email=email.strip().lower(), status="active"
        )
        if rows:
            return rows[0]
        return None

    async def find_active_by_product(
        self, product_id: str
    ) -> List[ProductNotificationsInternal]:
        return await self.storage.findAll(product_id=str(product_id), status="active")

    async def create_notification(
        self, product_id: str, email: str, user_id: Optional[str] = None
    ) -> Optional[ProductNotificationsInternal]:
        notification_data = ProductNotificationsInternalCreate(
            product_id=str(product_id),
            email=email.strip().lower(),
            user_id=str(user_id) if user_id else None,
            status="active",
        )
        existing = await self.find_active_by_product_and_email(product_id, email)
        if existing:
            return existing

        return await self.storage.create(notification_data)

    async def trigger_restock_notifications(self, product_id: str, product_name: str) -> None:
        active_notifs = await self.find_active_by_product(str(product_id))
        if not active_notifs:
            return

        domain = "http://localhost:3000"
        origins = settings.allowed_origins_list
        if origins:
            domain = origins[0]

        product_url = f"{domain}/customer/product/{product_id}"
        subject = f"Back in stock: {product_name}"
        clean_product_name = product_name.replace("'", "").replace('"', "")
        plain_text_body = f"Good news! The item {clean_product_name} is back in stock and ready to order. View the product here: {product_url}"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #ff3f6c;">Good news!</h2>
            <p>The item <strong>{clean_product_name}</strong> is back in stock!</p>
            <p>It is now restocked and ready for you to purchase. Grab yours before it runs out again!</p>
            <div style="margin: 30px 0; text-align: center;">
                <a href="{product_url}" style="display: inline-block; background-color: #ff3f6c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Product</a>
            </div>
            <hr style="border: none; border-top: 1px solid #eee;" />
            <p style="font-size: 12px; color: #888;">This is a one-time notification sent because you subscribed to restock alerts for this product at Stationery Junction.</p>
        </div>
        """

        import traceback
        from app.utils.logger import logger
        try:
            for notif in active_notifs:
                if notif.email:
                    # Send email
                    import asyncio
                    await asyncio.to_thread(email_service.send_email, notif.email, subject, plain_text_body, html_body=html_body)

                # In-app + push for logged-in users
                notif_user_id = notif.user_id
                if notif_user_id:
                    try:
                        from app.models.schemas import NotificationMetadata
                        from app.utils.notify import notify_user
                        await notify_user(
                            user_id    = str(notif_user_id),
                            notif_type = "back_in_stock",
                            title      = "Back in stock! 🎉",
                            message    = f"{product_name} is available again. Grab yours before it sells out!",
                            link       = f"/customer/products/product/{product_id}",
                            metadata   = NotificationMetadata(product_id=str(product_id), status="restocked"),
                        )
                    except Exception as push_err:
                        logger.warning("Restock push/in-app failed for user %s product %s: %s", notif_user_id, product_id, push_err)

                # Mark as notified
                await self.storage.update(notif.id, ProductNotificationsInternalUpdate(status="notified"))
        except Exception as e:
            logger.error(f"Restock notification crashed: {e}\n{traceback.format_exc()}")


product_notification_repository = ProductNotificationRepository()

