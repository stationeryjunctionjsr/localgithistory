import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "populated_order = await populate_order(order)" in line:
        print("".join(lines[i-15:i+10]))
        break
