with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "populated = []" in line:
        print(f"L{i}: {line.strip()}")
        break
