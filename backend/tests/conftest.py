import asyncio
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.repositories.user_repository import user_repository
from app.repositories.session_repository import session_repository

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for the async tests to share connections."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """Globally mock email service to avoid real SMTP calls and delays in tests."""
    from app.services.email_service import email_service
    monkeypatch.setattr(email_service, "send_email", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_email_with_attachment", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_verification_email", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_order_placed_email", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_order_delivered_email", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_privacy_policy_update_email", lambda *args, **kwargs: True)
    monkeypatch.setattr(email_service, "send_order_returned_email", lambda *args, **kwargs: True)

@pytest.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app (no network required)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def user_auth(client: AsyncClient):
    """Create a throwaway regular user, log in, yield auth headers, then clean up."""
    email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    user_data = {
        "name": "Test User",
        "email": email,
        "password": "password123",
        "role": "customer",
    }
    user = await user_repository.create(user_data)
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = response.json().get("token", "")
    if not token:
        print(f"DEBUG: Login failed for {email}. Status: {response.status_code}, Body: {response.text}")
    yield {"Authorization": f"Bearer {token}"}
    try:
        await session_repository.delete_all_for_user(user["_id"])
        await user_repository.storage.delete(user["_id"])
    except Exception:
        pass
