import pytest
import os
from unittest.mock import patch
from httpx import AsyncClient

from app.repositories.user_repository import user_repository


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, user_auth):
    # Set TESTING env var to allow fetching the code in response
    os.environ["TESTING"] = "true"

    # 1. Check profile is initially unverified
    res = await client.get("/api/users/profile", headers=user_auth)
    assert res.status_code == 200
    profile = res.json()
    assert profile.get("isEmailVerified") is False

    # 2. Request verification code
    res = await client.post("/api/users/request-email-verification", headers=user_auth)
    assert res.status_code == 200
    res_data = res.json()
    assert "code" in res_data
    code = res_data["code"]
    assert len(code) == 6

    # 3. Verify with wrong code should return 400
    res = await client.post("/api/users/verify-email", json={"code": "000000"}, headers=user_auth)
    assert res.status_code == 400

    # 4. Verify with correct code should return 200
    res = await client.post("/api/users/verify-email", json={"code": code}, headers=user_auth)
    assert res.status_code == 200
    assert res.json()["message"] == "Email verified successfully."

    # 5. Check profile is now verified
    res = await client.get("/api/users/profile", headers=user_auth)
    assert res.status_code == 200
    profile = res.json()
    assert profile.get("isEmailVerified") is True


@pytest.mark.asyncio
async def test_email_verification_reset_on_email_change(client: AsyncClient, user_auth):
    # Set profile to verified first
    res = await client.get("/api/users/profile", headers=user_auth)
    user_id = res.json()["_id"]
    await user_repository.update(user_id, {"isEmailVerified": True})

    # Verify it is true
    res = await client.get("/api/users/profile", headers=user_auth)
    assert res.json().get("isEmailVerified") is True

    # Update profile with same email (should not reset)
    email = res.json()["email"]
    res = await client.put(f"/api/users/{user_id}", json={"email": email, "name": "New Name"}, headers=user_auth)
    assert res.status_code == 200
    assert res.json().get("isEmailVerified") is True

    # Update profile with different email (should reset to false)
    import uuid

    new_email = f"new_verified_email_{uuid.uuid4().hex[:8]}@test.com"
    res = await client.put(f"/api/users/{user_id}", json={"email": new_email}, headers=user_auth)
    assert res.status_code == 200
    assert res.json().get("isEmailVerified") is False
