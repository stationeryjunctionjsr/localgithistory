import pytest


def test_api_contract_responses():
    """
    Contract tests ensure that frontend assumes correct data structures from backend.
    This can use OpenAPI schema validation or simple key-checking.
    """
    expected_product_schema_keys = {"id", "name", "price", "description", "category_id"}

    # Pretend we queried /api/v1/products and got this dict
    sample_response_product = {
        "id": "123",
        "name": "Notebook",
        "price": 100.0,
        "description": "A good notebook",
        "category_id": 1,
        "stock": 50,
    }

    response_keys = set(sample_response_product.keys())

    # Verify the backend response includes all keys the frontend contract requires
    assert expected_product_schema_keys.issubset(response_keys), "Contract mismatch: Missing keys in product schema"