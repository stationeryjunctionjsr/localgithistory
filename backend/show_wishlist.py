import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("app/routers/wishlist.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "def get_wishlist(" in line:
        print("".join(lines[i:i+60]))
        break
