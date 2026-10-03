import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("tests/test_delivery_zones_and_checkout.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
print("".join(lines[415:425]))
