from typing import Any, Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import OrderFeedbackInternal, OrderFeedbackInternalCreate, OrderFeedbackInternalUpdate

class OrderFeedbackRepository:
    def __init__(self):
        self.storage = get_storage("orderFeedback")

    async def findAll(self, query: Optional[Dict] = None) -> List[OrderFeedbackInternal]:
        return await self.storage.findAll(query or {})

    async def findById(self, id: str) -> Optional[OrderFeedbackInternal]:
        return await self.storage.findById(id)

    async def findByOrder(self, order_id: str) -> Optional[OrderFeedbackInternal]:
        return await self.storage.findOne({"orderId": order_id})

    async def findByUser(self, user_id: str) -> List[OrderFeedbackInternal]:
        return await self.storage.findAll({"userId": user_id})

    async def create(self, feedback_data: OrderFeedbackInternalCreate) -> OrderFeedbackInternal:
        if feedback_data.rating is not None:
            feedback_data.rating = int(feedback_data.rating)
        if feedback_data.delivery_rating is not None:
            feedback_data.delivery_rating = int(feedback_data.delivery_rating)
        
        if feedback_data.comment is None:
            feedback_data.comment = ""
        if feedback_data.delivery_comment is None:
            feedback_data.delivery_comment = ""
        if feedback_data.feedback_type is None:
            feedback_data.feedback_type = "order"

        return await self.storage.create(feedback_data)

    async def update(self, id: str, update_data: OrderFeedbackInternalUpdate) -> OrderFeedbackInternal:
        if update_data.rating is not None:
            update_data.rating = int(update_data.rating)
        if update_data.delivery_rating is not None:
            update_data.delivery_rating = int(update_data.delivery_rating)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


order_feedback_repository = OrderFeedbackRepository()
