from typing import Dict, Optional

from app.db.storage_factory import get_storage


class OrderFeedbackRepository:
    def __init__(self):
        self.storage = get_storage("orderFeedback")

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findByOrder(self, order_id: str):
        return await self.storage.findOne({"orderId": order_id})

    async def findByUser(self, user_id: str):
        return await self.storage.findAll({"userId": user_id})

    async def create(self, feedback_data: Any):
        feedback = {
            "orderId": feedback_data.get("orderId"),
            "userId": feedback_data["userId"],
            "rating": int(feedback_data["rating"]),  # 1-5
            "comment": feedback_data.get("comment", ""),
            "deliveryRating": int(feedback_data["deliveryRating"]) if feedback_data.get("deliveryRating") else None,
            "deliveryComment": feedback_data.get("deliveryComment", ""),
            "feedbackType": feedback_data.get("feedbackType", "order"),
        }

        return await self.storage.create(feedback)

    async def update(self, id: str, update_data: Any):
        if "rating" in update_data:
            update_data.rating = int(update_data.rating)
        if "deliveryRating" in update_data and update_data.deliveryRating:
            update_data.deliveryRating = int(update_data.deliveryRating)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


order_feedback_repository = OrderFeedbackRepository()
