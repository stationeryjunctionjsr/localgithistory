import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository
from app.repositories.payment_repository import payment_repository
from app.repositories.order_repository import order_repository
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_wholesaler_dues_and_block_flow(client: AsyncClient):
    # 1. Create a Wholesaler User
    email = f"wholesaler_{uuid.uuid4().hex[:8]}@test.com"
    user_data = UserCreate(
        name="Test Wholesaler",
        email=email,
        password="password123",
        role="wholesaler",
        paymentTerms="30",
        creditLimit=10000.0,
        creditUsed=0.0,
        approvalStatus="approved",
    )
    user = await user_repository.create(user_data)

    # Login
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = response.json().get("token", "")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 2. Get initial dues (should be empty/zero)
        response = await client.get("/api/payments/dues", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["hasOverdueBills"] is False
        assert data["totalDues"] == 0
        assert len(data["bills"]) == 0

        # 3. Create an overdue credit payment (35 days ago)
        order_date = datetime.now(timezone.utc) - timedelta(days=35)

        # Create corresponding order record via repository to generate IDs & number correctly
        order = await order_repository.create(
            {
                "user": user.id,
                "userRole": "wholesaler",
                "subtotal": 500.0,
                "total": 500.0,
                "orderType": "wholesaler",
                "paymentMethod": "credit",
                "status": "processing",
                "createdAt": order_date.isoformat().replace("+00:00", "Z"),
            }
        )

        payment_data = {
            "orderId": order.id,
            "userId": str(user.id),
            "customerName": user.name,
            "orderDate": order_date.isoformat().replace("+00:00", "Z"),
            "paymentMethod": "credit",
            "amountPaid": 0.0,
            "amountRemaining": 500.0,
            "totalAmount": 500.0,
        }
        payment = await payment_repository.create(payment_data)

        # 4. Fetch dues again (should show 500 dues and hasOverdueBills = True)
        response = await client.get("/api/payments/dues", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["hasOverdueBills"] is True
        assert data["totalDues"] == 500.0
        assert len(data["bills"]) == 1
        assert data["bills"][0]["overdue"] is True
        assert "Overdue by 5 days" in data["bills"][0]["timeRemaining"]

        # 5. Placing order should be blocked
        order_payload = {
            "shippingAddress": {
                "street": "123 Business St",
                "city": "Mumbai",
                "state": "Maharashtra",
                "zipCode": "400001",
                "district": "Mumbai",
                "country": "India",
                "name": "Business Office",
            },
            "paymentMethod": "credit",
            "items": [{"productId": "1", "quantity": 1, "price": 100}],
        }
        response = await client.post("/api/orders/", headers=headers, json=order_payload)
        print(response.json())
        assert response.status_code == 400
        assert "pending dues" in response.json()["detail"]

        # 6. Submit a payment screenshot (verified = False)
        # Settle credit endpoint: POST /api/orders/{order_id}/settle-credit
        # This will add an unverified payment entry.
        settle_response = await client.post(
            f"/api/orders/{payment.order_id}/settle-credit",
            headers=headers,
            json={
                "amount": 500.0,
                "paymentImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            },
        )
        assert settle_response.status_code == 200

        # 7. Fetch dues again. Because the entry is not verified, it should STILL be overdue!
        response = await client.get("/api/payments/dues", headers=headers)
        data = response.json()
        assert data["hasOverdueBills"] is True
        assert data["totalDues"] == 500.0

        # 8. Manually verify the payment entry (simulating admin verification)
        updated_payment = await payment_repository.findById(payment.id)
        entries = updated_payment.payment_entries or []
        assert len(entries) == 1
        entry_id = entries[0].entry_id

        # Verify the entry via repository update
        await payment_repository.updatePaymentEntry(payment.id, entry_id, {"verified": True})

        # 9. Fetch dues again. Now it should be cleared!
        response = await client.get("/api/payments/dues", headers=headers)
        data = response.json()
        assert data["hasOverdueBills"] is False
        assert data["totalDues"] == 0.0

        # 10. Placing order should no longer block on dues (will fail on empty cart/other checks, not dues block)
        response = await client.post("/api/orders/", headers=headers, json=order_payload)
        assert "pending dues" not in response.json().get("detail", "")

    finally:
        # Cleanup
        from app.repositories.session_repository import session_repository

        if "user" in locals():
            try:
                await session_repository.delete_all_for_user(user.id)
            except Exception:
                pass
            try:
                await user_repository.storage.delete(user.id)
            except Exception:
                pass
        if "payment" in locals():
            try:
                await payment_repository.delete(payment.id)
            except Exception:
                pass
        if "order" in locals():
            try:
                await order_repository.delete(order.id)
            except Exception:
                pass
