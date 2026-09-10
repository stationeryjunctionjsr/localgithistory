from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.mysql_flat_base_dao import MySQLFlatBaseDAO


class MySQLCustomerSegmentDAO(MySQLFlatBaseDAO):
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

    def _row_to_dict(self, r) -> Dict:
        doc = super()._row_to_dict(r)
        if hasattr(r, 'external_id') and r.external_id:
            doc['externalId'] = r.external_id
        return doc

    def _flatten_filters(self, data: Dict) -> Dict:
        # Move keys from 'filters' directly into data so they get mapped by scalar_map
        if "filters" in data and isinstance(data["filters"], dict):
            for k, v in data["filters"].items():
                data[k] = v
            del data["filters"]
        return data

    def _unflatten_filters(self, data: Dict) -> Dict:
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
            if k in data and data[k] is not None:
                filters[k] = data.pop(k)
        if filters:
            data["filters"] = filters
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

    async def create(self, data: Dict) -> Dict:
        data = self._flatten_filters(data)
        user_ids = data.pop("userIds", [])
        created = await super().create(data)
        if created and "externalId" in created:
            await self._save_user_ids(created["externalId"], user_ids)
            created["userIds"] = await self._fetch_user_ids(created["externalId"])
            created = self._unflatten_filters(created)
        return created

    async def update(self, id: str, data: Dict) -> Dict:
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
