import re

with open('tests/test_returns_e2e.py', 'r', encoding='utf-8') as f:
    text = f.read()

debug_code = """
    # Debug DB
    db_order = await order_repository.findById(order_id)
    print("DB ORDER:", db_order)
    db_prod = await product_repository.findById(prod_id)
    print("DB PRODUCT:", db_prod)
    from app.repositories.category_repository import category_repository
    db_cat = await category_repository.findByName(db_prod.category)
    print("DB CAT:", db_cat)
    
    print("ELIGIBILITY RESULT:", eligibility)
    assert len(eligibility["eligibleItems"]) > 0, f"No items eligible for return! Reason: {eligibility.get('reason')}"
"""

text = text.replace(
    'print("ELIGIBILITY RESULT:", eligibility)\n    assert len(eligibility["eligibleItems"]) > 0, f"No items eligible for return! Reason: {eligibility.get(\'reason\')}"',
    debug_code
)

with open('tests/test_returns_e2e.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
