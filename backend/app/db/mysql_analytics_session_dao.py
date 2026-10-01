import logging
from typing import Optional
from datetime import datetime
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.schemas import AnalyticsSessionCreate, AnalyticsSessionResponse

logger = logging.getLogger(__name__)

class MySQLAnalyticsSessionDAO:
    @property
    def TABLE(self):
        return "sj_analytics_sessions"

    def _factory(self):
        return get_async_session_factory()

    async def create_session(self, session_data: AnalyticsSessionCreate) -> Optional[AnalyticsSessionResponse]:
        query = f"""
            INSERT IGNORE INTO {self.TABLE}
            (session_id, user_id, source, os, browser, ip_address, device_type, device_os_version, device_model, device_app_version, campaign, start_time, end_time, time_spent_seconds)
            VALUES (:session_id, :user_id, :source, :os, :browser, :ip_address, :device_type, :device_os_version, :device_model, :device_app_version, :campaign, :start_time, :end_time, 0)
        """
        params = {
            "session_id": session_data.session_id,
            "user_id": session_data.user_id,
            "source": session_data.source,
            "os": session_data.os,
            "browser": session_data.browser,
            "ip_address": session_data.ip_address,
            "device_type": session_data.device_type,
            "device_os_version": session_data.device_os_version,
            "device_model": session_data.device_model,
            "device_app_version": session_data.device_app_version,
            "campaign": session_data.campaign,
            "start_time": session_data.start_time,
            "end_time": session_data.start_time
        }
        
        factory = self._factory()
        try:
            async with factory() as session:
                await session.execute(text(query), params)
                await session.commit()
            return await self.get_session(session_data.session_id)
        except Exception as e:
            logger.error(f"Error creating analytics session: {e}")
            return None

    async def update_session_time(self, session_id: str, new_end_time: datetime) -> bool:
        query = f"""
            UPDATE {self.TABLE}
            SET end_time = :new_end_time,
                time_spent_seconds = TIMESTAMPDIFF(SECOND, start_time, :new_end_time)
            WHERE session_id = :session_id AND end_time < :new_end_time
        """
        params = {
            "new_end_time": new_end_time,
            "session_id": session_id
        }
        
        factory = self._factory()
        try:
            async with factory() as session:
                res = await session.execute(text(query), params)
                await session.commit()
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating analytics session time: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[AnalyticsSessionResponse]:
        query = f"SELECT * FROM {self.TABLE} WHERE session_id = :session_id LIMIT 1"
        factory = self._factory()
        try:
            async with factory() as session:
                res = await session.execute(text(query), {"session_id": session_id})
                row = res.fetchone()
                if row:
                    return AnalyticsSessionResponse(
                        id=row.id,
                        session_id=row.session_id,
                        user_id=row.user_id,
                        source=row.source,
                        os=row.os,
                        browser=row.browser,
                        ip_address=row.ip_address,
                        device_type=row.device_type,
                        device_os_version=row.device_os_version,
                        device_model=row.device_model,
                        device_app_version=row.device_app_version,
                        campaign=row.campaign,
                        start_time=row.start_time,
                        end_time=row.end_time,
                        time_spent_seconds=row.time_spent_seconds
                    )
                return None
        except Exception as e:
            logger.error(f"Error fetching analytics session: {e}")
            return None
