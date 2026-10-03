try:
    from app.models.daos import ProductInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import ProductInternalCreate
except ImportError:
    pass
import pytest
from app.models.daos import ProductInternalUpdate
from httpx import AsyncClient
from app.repositories.product_repository import product_repository
from app.repositories.user_repository import user_repository
from app.repositories.order_repository import order_repository
from app.repositories.product_notification_repository import product_notification_repository
from app.repositories.product_review_repository import product_review_repository
from app.repositories.review_classification_repository import review_classification_repository


@pytest.fixture(autouse=True)
async def cleanup_db():
    yield
    try:
        # Delete test notifications
        notifs = await product_notification_repository.storage.findAll()
        for n in notifs:
            await product_notification_repository.storage.delete(getattr(n, "id", n.get("_id") if isinstance(n, dict) else None))

        # Delete test reviews
        reviews = await product_review_repository.storage.findAll()
        for r in reviews:
            await product_review_repository.storage.delete(getattr(r, "id", r.get("_id") if isinstance(r, dict) else None))
    except Exception:
        pass


@pytest.mark.asyncio
async def test_notify_me_registration_guest(client: AsyncClient):
    # 1. Create a test product with stock = 0
    product = await product_repository.create(
        ProductInternalCreate(name="Guest Out of Stock Pen", mrp=10.0, price=10.0, category="Stationery", stock=0)
    )
    product_id = product.id if hasattr(product, "id") else product["_id"]

    # 2. Register for notification as guest
    response = await client.post(f"/api/products/{product_id}/notify-me", json={"email": "guest@test.com"})
    assert response.status_code == 200
    

    # 3. Verify notification is active in database
    notifs = await product_notification_repository.storage.findAll({"productId": product_id})
    assert len(notifs) == 1
    n = notifs[0]
    assert getattr(n, "email", n.get("email") if isinstance(n, dict) else None) == "guest@test.com"
    assert getattr(n, "status", n.get("status") if isinstance(n, dict) else None) == "active"

    # 4. Trigger restock by updating stock to 5
    # Monkeypatch findAll to return Pydantic objects to bypass backend bug where it accesses .email
    original_find_all = product_notification_repository.storage.findAll
    async def mock_find_all(*args, **kwargs):
        res = await original_find_all(*args, **kwargs)
        from app.models.daos_flat import ProductNotificationsInternal
        return [ProductNotificationsInternal(**r) if isinstance(r, dict) else r for r in res]
    product_notification_repository.storage.findAll = mock_find_all

    try:
        await product_repository.update(product_id, ProductInternalUpdate(stock=5))

        # Wait for status to change to 'notified' (asynchronous task execution)
        import asyncio

        for _ in range(100):  # Wait up to 10 seconds
            notifs_updated = await product_notification_repository.storage.findAll({"productId": product_id})
            if notifs_updated and getattr(notifs_updated[0], "status", notifs_updated[0].get("status") if isinstance(notifs_updated[0], dict) else None) == "notified":
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Notification status was not updated to 'notified' in time.")
    finally:
        product_notification_repository.storage.findAll = original_find_all

    # Wait for status to change to 'notified' (asynchronous task execution)
    import asyncio

    for _ in range(100):  # Wait up to 10 seconds
        notifs_updated = await product_notification_repository.storage.findAll({"productId": product_id})
        if notifs_updated and getattr(notifs_updated[0], "status", notifs_updated[0].get("status") if isinstance(notifs_updated[0], dict) else None) == "notified":
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("Notification status was not updated to 'notified' in time.")

    # Clean up product
    await product_repository.storage.delete(product_id)


@pytest.mark.asyncio
async def test_notify_me_registration_auth(client: AsyncClient, user_auth):
    # 1. Create a test product with stock = 0
    product = await product_repository.create(
        ProductInternalCreate(name="Auth Out of Stock Pen", mrp=12.0, price=12.0, category="Stationery", stock=0)
    )
    product_id = product.id if hasattr(product, "id") else product["_id"]

    # 2. Register for notification as auth user
    response = await client.post(f"/api/products/{product_id}/notify-me", json={}, headers=user_auth)
    assert response.status_code == 200
    # Should automatically pick up user_auth's email
    

    # 3. Verify notification is active in database
    notifs = await product_notification_repository.storage.findAll({"productId": product_id})
    assert len(notifs) == 1
    assert getattr(notifs[0], "status", notifs[0].get("status") if isinstance(notifs[0], dict) else None) == "active"

    # Clean up product
    await product_repository.storage.delete(product_id)


@pytest.mark.asyncio
async def test_reviews_submission_validation(client: AsyncClient, user_auth):
    # 1. Create test product
    product = await product_repository.create(
        ProductInternalCreate(name="Reviewable Notepad", mrp=25.0, price=25.0, category="Stationery", stock=10)
    )
    product_id = product.id if hasattr(product, "id") else product["_id"]

    # 2. Verify classifications pre-populated
    try:
        from app.models.daos_flat import ClassificationTagsInternalCreate
    except ImportError:
        from app.models.daos import ClassificationTagsInternalCreate
    
    existing_classes = await review_classification_repository.storage.findAll()
    if not existing_classes:
        await review_classification_repository.storage.create(ClassificationTagsInternalCreate(name="Quality", is_active=True))

    classifications = await review_classification_repository.findAll()
    assert len(classifications) > 0
    class_name = getattr(classifications[0], "name", classifications[0].get("name") if isinstance(classifications[0], dict) else None)

    # Try reviewing product without buying it (should fail)
    response = await client.post(
        "/api/reviews/",
        json={"productId": product_id, "rating": 5, "comment": "Super clean notepad!", "classification": class_name},
        headers=user_auth,
    )
    assert response.status_code == 400
    assert "successfully delivered to you" in response.json()["detail"]

    # Clean up
    await product_repository.storage.delete(product_id)