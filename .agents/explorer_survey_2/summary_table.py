import json
from collections import Counter

with open("c:/Ecommerce app/.agents/explorer_survey_2/classified_calls.json", "r", encoding="utf-8") as f:
    calls = json.load(f)

by_file = {}
for c in calls:
    by_file.setdefault(c["file"], []).append(c)

print(f"{'File':30s} | {'Cat A':6s} | {'Cat B':6s} | {'(B-Route)':10s} | {'(B-Other)':10s} | {'Total':6s}")
print("-" * 80)

total_a = 0
total_b = 0
total_b_route = 0
total_b_other = 0
total_all = 0

for fname in sorted(by_file.keys()):
    fcalls = by_file[fname]
    ca = sum(1 for c in fcalls if c["category"] == "Category A")
    cb = sum(1 for c in fcalls if c["category"] == "Category B")
    cb_route = sum(1 for c in fcalls if c["caller"] in ("router", "app"))
    cb_other = cb - cb_route
    tot = len(fcalls)
    total_a += ca
    total_b += cb
    total_b_route += cb_route
    total_b_other += cb_other
    total_all += tot
    print(f"{fname:30s} | {ca:6d} | {cb:6d} | {cb_route:10d} | {cb_other:10d} | {tot:6d}")

print("-" * 80)
print(f"{'TOTAL':30s} | {total_a:6d} | {total_b:6d} | {total_b_route:10d} | {total_b_other:10d} | {total_all:6d}")
