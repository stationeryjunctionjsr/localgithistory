import pytest
from app.repositories.category_repository import category_repository


@pytest.fixture(autouse=True)
async def cleanup_categories():
    yield
    try:
        categories = await category_repository.storage.findAll()
        for cat in categories:
            if cat.get("name", "").startswith("TEST_CAT_OPT_"):
                await category_repository.storage.delete(cat["_id"])
    except Exception:
        pass


@pytest.mark.asyncio
async def test_category_optimizations():
    # 1. Create test categories
    c1 = await category_repository.create(
        {
            "name": "TEST_CAT_OPT_Pen",
            "description": "Category for pens",
            "categoryTag": "stationery",
            "isActive": True,
            "isReturnable": True,
        }
    )
    c2 = await category_repository.create(
        {
            "name": "TEST_CAT_OPT_Paper",
            "description": "Category for paper",
            "categoryTag": "stationery",
            "isActive": False,
            "isReturnable": False,
        }
    )

    # 2. Test exact name lookup
    found_pen = await category_repository.findByName("TEST_CAT_OPT_Pen")
    assert found_pen is not None
    assert found_pen["_id"] == c1["_id"]

    # 3. Test case-insensitive name lookup
    found_pen_lower = await category_repository.findByName("test_cat_opt_pen")
    assert found_pen_lower is not None
    assert found_pen_lower["_id"] == c1["_id"]

    # 4. Test filtering on other fields at DB level
    # Filter by isActive
    active_cats = await category_repository.storage.findAll({"isActive": True})
    active_cats = [c for c in active_cats if c["name"].startswith("TEST_CAT_OPT_")]
    assert len(active_cats) == 1
    assert active_cats[0]["name"] == "TEST_CAT_OPT_Pen"

    inactive_cats = await category_repository.storage.findAll({"isActive": False})
    inactive_cats = [c for c in inactive_cats if c["name"].startswith("TEST_CAT_OPT_")]
    assert len(inactive_cats) == 1
    assert inactive_cats[0]["name"] == "TEST_CAT_OPT_Paper"

    # Filter by isReturnable
    returnable_cats = await category_repository.storage.findAll({"isReturnable": True})
    returnable_cats = [c for c in returnable_cats if c["name"].startswith("TEST_CAT_OPT_")]
    assert len(returnable_cats) == 1
    assert returnable_cats[0]["name"] == "TEST_CAT_OPT_Pen"
