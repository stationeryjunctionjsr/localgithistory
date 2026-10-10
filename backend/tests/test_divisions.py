import pytest
from app.repositories.division_repository import division_repository
from app.repositories.category_tag_repository import category_tag_repository
from app.models.division import DivisionInternalCreate, DivisionInternalUpdate
from app.models.daos_flat import CategoryTagInternalCreate, CategoryTagInternalUpdate


@pytest.mark.asyncio
async def test_get_active_divisions(client):
    """Test active divisions endpoint returns 200 and list of active divisions."""
    response = await client.get("/api/divisions/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [d.get("name") for d in data]
    assert "Stationery" in names


@pytest.mark.asyncio
async def test_get_division_tags(client):
    """Test fetching category tags under a specific division."""
    div = await division_repository.findByName("Stationery")
    assert div is not None
    response = await client.get(f"/api/divisions/{div.id}/tags")
    assert response.status_code == 200
    tags = response.json()
    assert isinstance(tags, list)
    tag_names = [t.get("name") for t in tags]
    assert "Writing Instruments" in tag_names


@pytest.mark.asyncio
async def test_get_active_category_tags_with_division(client):
    """Test active category tags endpoint returns tags with division info."""
    response = await client.get("/api/category-tags/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    writing_tag = next((t for t in data if t.get("name") == "Writing Instruments"), None)
    assert writing_tag is not None
    assert writing_tag.get("divisionName") == "Stationery" or writing_tag.get("categoryHeadName") == "Stationery"


@pytest.mark.asyncio
async def test_division_repository_crud():
    """Test repository create, update, and deletion of a Division."""
    test_div_name = "Test Automated Division"
    # Clean up if leftover
    existing = await division_repository.findByName(test_div_name)
    if existing:
        await division_repository.hardDelete(existing.id)

    # Create
    created = await division_repository.create(
        DivisionInternalCreate(
            name=test_div_name,
            description="Testing automated CRUD for division",
            display_order=99,
            is_active=True,
        )
    )
    assert created is not None
    assert created.name == test_div_name

    # Update
    updated = await division_repository.update(
        created.id,
        DivisionInternalUpdate(description="Updated division description"),
    )
    assert updated.description == "Updated division description"

    # Delete
    deleted = await division_repository.hardDelete(created.id)
    assert deleted is True

    # Verify not found
    found = await division_repository.findById(created.id)
    assert found is None
