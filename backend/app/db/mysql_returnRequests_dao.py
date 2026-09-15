import pymysql.cursors
from typing import List, Optional, Any
from pydantic import BaseModel

class ReturnRequestItemResponse(BaseModel):
    productId: str
    quantity: int
    condition: str

class ReturnRequestResponse(BaseModel):
    id: str
    orderId: str
    userId: str
    reason: str
    comments: Optional[str] = None
    status: str
    adminComments: Optional[str] = None
    refundAmount: Optional[float] = None
    isRestocked: bool
    items: List[ReturnRequestItemResponse] = []
    images: List[str] = []

class MySQLReturnrequestsDAO:
    def __init__(self, connection):
        self.connection = connection

    def create(self, data: Any) -> ReturnRequestResponse:
        with self.connection.cursor() as cursor:
            sql = """
            INSERT INTO sj_return_requests 
            (id, order_id, user_id, reason, comments, status, admin_comments, refund_amount, is_restocked)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data.id,
                data.orderId,
                data.userId,
                data.reason,
                data.comments,
                data.status,
                data.adminComments,
                data.refundAmount,
                1 if data.isRestocked else 0
            ))

            if data.items:
                item_sql = """
                INSERT INTO sj_return_request_items (return_request_id, product_id, quantity, `condition`)
                VALUES (%s, %s, %s, %s)
                """
                for item in data.items:
                    cursor.execute(item_sql, (
                        data.id,
                        item.productId,
                        item.quantity,
                        item.condition
                    ))

            if data.images:
                image_sql = """
                INSERT INTO sj_return_request_images (return_request_id, image_url)
                VALUES (%s, %s)
                """
                for image in data.images:
                    cursor.execute(image_sql, (
                        data.id,
                        image
                    ))

            self.connection.commit()
            return self.findById(data.id)

    def update(self, id: str, data: Any) -> Optional[ReturnRequestResponse]:
        with self.connection.cursor() as cursor:
            fields = []
            values = []

            if data.orderId is not None:
                fields.append("order_id = %s")
                values.append(data.orderId)
            if data.userId is not None:
                fields.append("user_id = %s")
                values.append(data.userId)
            if data.reason is not None:
                fields.append("reason = %s")
                values.append(data.reason)
            if data.comments is not None:
                fields.append("comments = %s")
                values.append(data.comments)
            if data.status is not None:
                fields.append("status = %s")
                values.append(data.status)
            if data.adminComments is not None:
                fields.append("admin_comments = %s")
                values.append(data.adminComments)
            if data.refundAmount is not None:
                fields.append("refund_amount = %s")
                values.append(data.refundAmount)
            if data.isRestocked is not None:
                fields.append("is_restocked = %s")
                values.append(1 if data.isRestocked else 0)

            if fields:
                sql = f"UPDATE sj_return_requests SET {', '.join(fields)} WHERE id = %s"
                values.append(id)
                cursor.execute(sql, tuple(values))

            if data.items is not None:
                cursor.execute("DELETE FROM sj_return_request_items WHERE return_request_id = %s", (id,))
                item_sql = """
                INSERT INTO sj_return_request_items (return_request_id, product_id, quantity, `condition`)
                VALUES (%s, %s, %s, %s)
                """
                for item in data.items:
                    cursor.execute(item_sql, (
                        id,
                        item.productId,
                        item.quantity,
                        item.condition
                    ))

            if data.images is not None:
                cursor.execute("DELETE FROM sj_return_request_images WHERE return_request_id = %s", (id,))
                image_sql = """
                INSERT INTO sj_return_request_images (return_request_id, image_url)
                VALUES (%s, %s)
                """
                for image in data.images:
                    cursor.execute(image_sql, (
                        id,
                        image
                    ))

            self.connection.commit()
            return self.findById(id)

    def delete(self, id: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM sj_return_request_images WHERE return_request_id = %s", (id,))
            cursor.execute("DELETE FROM sj_return_request_items WHERE return_request_id = %s", (id,))
            cursor.execute("DELETE FROM sj_return_requests WHERE id = %s", (id,))
            self.connection.commit()
            return cursor.rowcount > 0

    def findById(self, id: str) -> Optional[ReturnRequestResponse]:
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM sj_return_requests WHERE id = %s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._map_row(cursor, row)

    def findOne(self, filters: dict) -> Optional[ReturnRequestResponse]:
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if not filters:
                return None
            where_clauses = []
            values = []
            for k, v in filters.items():
                where_clauses.append(f"{k} = %s")
                values.append(v)
            sql = f"SELECT * FROM sj_return_requests WHERE {' AND '.join(where_clauses)} LIMIT 1"
            cursor.execute(sql, tuple(values))
            row = cursor.fetchone()
            if not row:
                return None
            return self._map_row(cursor, row)

    def findAll(self, filters: dict = None) -> List[ReturnRequestResponse]:
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM sj_return_requests"
            values = []
            if filters:
                where_clauses = []
                for k, v in filters.items():
                    where_clauses.append(f"{k} = %s")
                    values.append(v)
                sql += f" WHERE {' AND '.join(where_clauses)}"
            cursor.execute(sql, tuple(values))
            rows = cursor.fetchall()
            return [self._map_row(cursor, row) for row in rows]

    def _map_row(self, cursor, row: dict) -> ReturnRequestResponse:
        req_id = row['id']

        # items
        cursor.execute("SELECT product_id, quantity, `condition` FROM sj_return_request_items WHERE return_request_id = %s", (req_id,))
        items_rows = cursor.fetchall()
        items = [
            ReturnRequestItemResponse(
                productId=item['product_id'],
                quantity=item['quantity'],
                condition=item['condition']
            ) for item in items_rows
        ]

        # images
        cursor.execute("SELECT image_url FROM sj_return_request_images WHERE return_request_id = %s", (req_id,))
        images_rows = cursor.fetchall()
        images = [img['image_url'] for img in images_rows]

        return ReturnRequestResponse(
            id=row['id'],
            orderId=row['order_id'],
            userId=row['user_id'],
            reason=row['reason'],
            comments=(row['comments'] if 'comments' in row else None),
            status=row['status'],
            adminComments=(row['admin_comments'] if 'admin_comments' in row else None),
            refundAmount=(row['refund_amount'] if 'refund_amount' in row else None),
            isRestocked=bool(row['is_restocked']),
            items=items,
            images=images
        )
