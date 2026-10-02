import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository

@pytest.mark.asyncio
async def test_seller_payout_flow():
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller_email = f"seller_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
    seller = await user_repository.create(UserCreate(name="Seller", email=seller_email, password="pass", role="seller", isSellerAdmin=True))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        admin_auth = await login(admin_email)
        seller_auth = await login(seller_email)

        # Create Seller Payout
        payout_payload = {
            "sellerId": str(seller.id),
            "amount": 1500.0,
            "periodStart": "2024-01-01T00:00:00Z",
            "periodEnd": "2024-01-31T23:59:59Z",
            "subOrderIds": []
        }
        res = await client.post("/api/seller-payouts/", json=payout_payload, headers=admin_auth)
        assert res.status_code == 201, res.text
        payout_id = res.json()["id"]

        # Admin Mark Paid
        res = await client.post(f"/api/seller-payouts/{payout_id}/mark-paid", json={"paymentMethod": "bank_transfer", "paymentReference": "txn_123"}, headers=admin_auth)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "admin_paid"

        # Seller Mark Received
        res = await client.post(f"/api/seller-payouts/{payout_id}/mark-received", headers=seller_auth)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "seller_received"

@pytest.mark.asyncio
async def test_valet_payout_flow():
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    valet_email = f"valet_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
    valet = await user_repository.create(UserCreate(name="Valet", email=valet_email, password="pass", role="valet", isApproved=True, isOnDuty=True))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        admin_auth = await login(admin_email)
        valet_auth = await login(valet_email)

        # Create Valet Payout
        payout_payload = {
            "valetId": str(valet.id),
            "amount": 500.0,
            "periodStart": "2024-01-01T00:00:00Z",
            "periodEnd": "2024-01-31T23:59:59Z",
            "deliveryCount": 10,
            "returnCount": 2,
            }
        res = await client.post("/api/valet-payouts/payouts", json=payout_payload, headers=admin_auth)
        assert res.status_code == 201, res.text
        payout_id = res.json()["id"]

        # Admin Mark Paid
        res = await client.post(f"/api/valet-payouts/payouts/{payout_id}/mark-paid", json={"paymentMethod": "bank_transfer", "paymentReference": "txn_valet_123"}, headers=admin_auth)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "admin_paid"

        # Valet Mark Received
        res = await client.post(f"/api/valet-payouts/payouts/{payout_id}/mark-received", headers=valet_auth)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "valet_received"