from typing import List, Optional, Any
# Assuming DeviceSubscriptionResponse is importable from schemas or models.
# Adjust the import path based on the project's actual structure.
from app.schemas.deviceSubscription import DeviceSubscriptionResponse

class MySQLDevicesubscriptionsDAO:
    """
    Standalone DAO for deviceSubscriptions mapped to sj_device_subscriptions.
    """
    def __init__(self, connection):
        self.connection = connection

    def create(self, data: Any) -> DeviceSubscriptionResponse:
        cursor = self.connection.cursor(dictionary=True)
        query = """
            INSERT INTO sj_device_subscriptions (
                user_id, fcm_token, device_type, is_active
            ) VALUES (
                %s, %s, %s, %s
            )
        """
        values = (
            data.userId,
            data.fcmToken,
            data.deviceType,
            data.isActive
        )
        cursor.execute(query, values)
        self.connection.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return self.findById(last_id)

    def update(self, id: int, data: Any) -> Optional[DeviceSubscriptionResponse]:
        cursor = self.connection.cursor(dictionary=True)
        query = """
            UPDATE sj_device_subscriptions SET
                user_id = %s,
                fcm_token = %s,
                device_type = %s,
                is_active = %s
            WHERE id = %s
        """
        values = (
            data.userId,
            data.fcmToken,
            data.deviceType,
            data.isActive,
            id
        )
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()
        return self.findById(id)

    def delete(self, id: int) -> bool:
        cursor = self.connection.cursor(dictionary=True)
        query = "DELETE FROM sj_device_subscriptions WHERE id = %s"
        cursor.execute(query, (id,))
        affected_rows = cursor.rowcount
        self.connection.commit()
        cursor.close()
        return affected_rows > 0

    def findById(self, id: int) -> Optional[DeviceSubscriptionResponse]:
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT id, user_id, fcm_token, device_type, is_active FROM sj_device_subscriptions WHERE id = %s"
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return self._map_to_response(row)

    def findOne(self, **kwargs) -> Optional[DeviceSubscriptionResponse]:
        if not kwargs:
            return None
        cursor = self.connection.cursor(dictionary=True)
        conditions = []
        values = []
        for key, value in kwargs.items():
            column = self._map_field_to_column(key)
            conditions.append(f"{column} = %s")
            values.append(value)
            
        query = "SELECT id, user_id, fcm_token, device_type, is_active FROM sj_device_subscriptions WHERE " + " AND ".join(conditions) + " LIMIT 1"
        cursor.execute(query, tuple(values))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return self._map_to_response(row)
        
    def findAll(self, **kwargs) -> List[DeviceSubscriptionResponse]:
        cursor = self.connection.cursor(dictionary=True)
        if kwargs:
            conditions = []
            values = []
            for key, value in kwargs.items():
                column = self._map_field_to_column(key)
                conditions.append(f"{column} = %s")
                values.append(value)
            query = "SELECT id, user_id, fcm_token, device_type, is_active FROM sj_device_subscriptions WHERE " + " AND ".join(conditions)
            cursor.execute(query, tuple(values))
        else:
            query = "SELECT id, user_id, fcm_token, device_type, is_active FROM sj_device_subscriptions"
            cursor.execute(query)
            
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_response(row) for row in rows]

    def _map_field_to_column(self, field: str) -> str:
        mapping = {
            "userId": "user_id",
            "fcmToken": "fcm_token",
            "deviceType": "device_type",
            "isActive": "is_active",
            "id": "id"
        }
        return (mapping[field] if field in mapping else field)
        
    def _map_to_response(self, row: dict) -> DeviceSubscriptionResponse:
        return DeviceSubscriptionResponse(
            id=row["id"],
            userId=row["user_id"],
            fcmToken=row["fcm_token"],
            deviceType=row["device_type"],
            isActive=bool(row["is_active"]) if row["is_active"] is not None else None
        )
