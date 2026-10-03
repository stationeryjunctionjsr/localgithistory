import re
with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("populated_order = await populate_order(updated_parent)", """updated_parent = await order_repository.findById(str(order.id))
            print(f"DEBUG: updated_parent={updated_parent}")
            populated_order = await populate_order(updated_parent)
            print(f"DEBUG: populated_order={populated_order}")""")

with open("app/services/order_service.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Print added")
