import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("app/routers/payments.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
print("".join(lines[145:160]))
