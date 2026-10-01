import os
import subprocess
import sys

for i in range(3):
    print(f"Run {i+1}...")
    subprocess.run("python -m pytest -q tests/ > pytest_loop.txt", shell=True)
    
    # Run auto_fix_tests3.py (but modifying it slightly to read pytest_loop.txt)
    with open('auto_fix_tests3.py', 'r', encoding='utf-8') as f:
        script = f.read().replace('pytest_out_final.txt', 'pytest_loop.txt')
    with open('auto_fix_loop.py', 'w', encoding='utf-8') as f:
        f.write(script)
        
    res = subprocess.run("python auto_fix_loop.py", shell=True, capture_output=True, text=True)
    print(res.stdout)
    if "Fixed" not in res.stdout:
        print("No more fixes!")
        break
