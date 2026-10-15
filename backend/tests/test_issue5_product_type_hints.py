import typing
from app.routers.products import populate_product_discounts
from app.models.product import Product


def test_populate_product_discounts_type_hints():
    hints = typing.get_type_hints(populate_product_discounts)
    assert "products_list" in hints
    assert hints["products_list"] == typing.List[Product]
    assert hints["role"] is str
    assert hints["skinny"] is bool
