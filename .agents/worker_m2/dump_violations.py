import json

with open('.agents/explorer_survey_2/category_a_details.json') as f:
    data = json.load(f)

targets = ['delivery_charges.py', 'delivery_slots.py', 'delivery_zones.py', 'tracking.py', 'valet_availability.py', 'valet_payout.py']

for t in targets:
    items = data.get(t, [])
    print(f"=== {t} ({len(items)}) ===")
    for item in items:
        lineno = item['lineno']
        caller = item['caller']
        args = item['args']
        line_str = item['line_str'].strip()
        print(f"  L{lineno}: {caller}.get({args}) -> {line_str}")
