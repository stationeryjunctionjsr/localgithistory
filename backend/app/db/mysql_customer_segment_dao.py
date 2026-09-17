from typing import Dict
from app.models.customer_segment import CustomerSegment, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.mysql_flat_base_dao import MySQLFlatBaseDAO
from app.models.daos_flat import CustomerSegmentInternal, CustomerSegmentInternalCreate


class MySQLCustomerSegmentDAO(MySQLFlatBaseDAO):
    pydantic_model = CustomerSegmentInternal
    def __init__(self):
        super().__init__(
            table_name="sj_customer_segments",
            scalar_map={
                "type": "type",
                "name": "name",
                "description": "description",
                "isActive": "is_active",
                "isSystem": "is_system",
                "minAverageOrderValue": "min_avg_order_value",
                "maxAverageOrderValue": "max_avg_order_value",
                "startDate": "start_date",
                "endDate": "end_date",
                "minOrderFrequency": "min_order_freq",
                "maxOrderFrequency": "max_order_freq",
                "state": "state",
                "district": "district",
                "appUser": "app_user",
                "behavior": "behavior",
                "role": "role",
            },
            bool_api_keys=["isActive", "isSystem", "appUser"],
            has_external_id=True,
        )

    def __map_to_schema(self, r) -> Dict:
        doc = super().__map_to_schema(r)
        if r.external_id is not None and r.external_id:
            doc['externalId'] = r.external_id
        return doc

    def _flatten_filters(self, data: Any) -> Any:
        # Pydantic models already flatten the filters from the router before passing here
        return data

    def _unflatten_filters(self, data: Any) -> Any:
        # Move them back into 'filters' for the frontend
        filter_keys = [
            "minAverageOrderValue",
            "maxAverageOrderValue",
            "startDate",
            "endDate",
            "minOrderFrequency",
            "maxOrderFrequency",
            "state",
            "district",
            "appUser",
            "behavior",
            "role",
        ]
        filters = {}
        for k in filter_keys:
            if (isinstance(data, dict) and data.get(k) is not None) or (not isinstance(data, dict) and getattr(data, k, None) is not None):
                filters[k] = data.pop(k) if isinstance(data, dict) else getattr(data, k)
                if not isinstance(data, dict): setattr(data, k, None)
        if filters:
            if not isinstance(data, dict):
                setattr(data, 'filters', filters)
            else:
                data['filters'] = filters
        return data

    async def _fetch_user_ids(self, segment_id: str) -> List[str]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT user_id FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            return [r.user_id for r in result.fetchall()]

    async def _save_user_ids(self, segment_id: str, user_ids: List[str]):
        if user_ids is None:
            return
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            await session.execute(
                text("DELETE FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            if user_ids:
                params = [{"sid": segment_id, "uid": uid} for uid in user_ids]
                await session.execute(
                    text("INSERT INTO sj_customer_segment_users (segment_id, user_id) VALUES (:sid, :uid)"), params
                )
            await session.commit()

    async def findById(self, id: str) -> Optional[Dict]:
        doc = await super().findById(id)
        if doc:
            doc["userIds"] = await self._fetch_user_ids(doc["externalId"])
            doc = self._unflatten_filters(doc)
        return doc

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        docs = await super().findAll(query)
        for doc in docs:
            doc["userIds"] = await self._fetch_user_ids(doc["externalId"])
            self._unflatten_filters(doc)
        return docs

    async def create(self, data: Any) -> Any:
        data = self._flatten_filters(data)
        user_ids = data.pop("userIds", [])
        created = await super().create(data)
        if created and "externalId" in created:
            await self._save_user_ids(created["externalId"], user_ids)
            created["userIds"] = await self._fetch_user_ids(created["externalId"])
            created = self._unflatten_filters(created)
        return created

    async def update(self, id: str, data: Any) -> Any:
        data = self._flatten_filters(data)
        user_ids = None
        if "userIds" in data:
            user_ids = data.pop("userIds")

        updated = await super().update(id, data)
        if updated and user_ids is not None:
            await self._save_user_ids(id, user_ids)
            updated["userIds"] = await self._fetch_user_ids(id)
        elif updated:
            updated["userIds"] = await self._fetch_user_ids(id)

        if updated:
            updated = self._unflatten_filters(updated)
        return updated
