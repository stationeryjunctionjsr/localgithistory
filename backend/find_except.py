with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    text = f.read()
if "except Exception" in text[text.find("def populate_orders"):text.find("def populate_order")]:
    print("Found except inside populate_orders")
else:
    print("No except inside populate_orders")
