import pytest
from app.repositories.category_head_repository import category_head_repository
from app.repositories.category_tag_repository import category_tag_repository
from app.models.category_head import CategoryHeadInternalCreate, CategoryHeadInternalUpdate
from app.models.daos_flat import CategoryTagInternalCreate, CategoryTagInternalUpdate


@pytest.mark.asyncio
async def test_get_active_category_heads(client):
    """Test active category heads endpoint returns 200 and list of active heads."""
    response = await client.get("/api/category-heads/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [h.get("name") for h in data]
    assert "Stationery" in names


@pytest.mark.asyncio
async def test_get_category_heads_tags(client):
    """Test fetching category tags under a specific category head."""
    # Find Stationery head
    head = await category_head_repository.findByName("Stationery")
    assert head is not None
    response = await client.get(f"/api/category-heads/{head.id}/tags")
    assert response.status_code == 200
    tags = response.json()
    assert isinstance(tags, list)
    tag_names = [t.get("name") for t in tags]
    assert "Writing Instruments" in tag_names


@pytest.mark.asyncio
async def test_get_active_category_tags(client):
    """Test active category tags endpoint returns tags with category_head info."""
    response = await client.get("/api/category-tags/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    writing_tag = next((t for t in data if t.get("name") == "Writing Instruments"), None)
    assert writing_tag is not None
    assert writing_tag.get("categoryHeadName") == "Stationery"


@pytest.mark.asyncio
async def test_category_head_repository_crud():
    """Test repository create, update, and deletion of a Category Head."""
    test_head_name = "Test Automated Head"
    # Clean up if leftover
    existing = await category_head_repository.findByName(test_head_name)
    if existing:
        await category_head_repository.hardDelete(existing.id)

    # Create
    created = await category_head_repository.create(
        CategoryHeadInternalCreate(
            name=test_head_name,
            description="Testing automated CRUD",
            display_order=99,
            is_active=True,
        )
    )
    assert created is not None
    assert created.name == test_head_name

    # Update
    updated = await category_head_repository.update(
        created.id,
        CategoryHeadInternalUpdate(description="Updated description"),
    )
    assert updated.description == "Updated description"

    # Delete
    deleted = await category_head_repository.hardDelete(created.id)
    assert deleted is True

    # Verify not found
    found = await category_head_repository.findById(created.id)
    assert found is None
