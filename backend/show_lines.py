import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
print("".join(lines[1410:1430]))
