import json

with open("c:/Ecommerce app/.agents/explorer_survey_2/category_a_details.json", "r", encoding="utf-8") as f:
    cat_a = json.load(f)

for fname, calls in sorted(cat_a.items()):
    funcs = sorted(list(set(c["func"] for c in calls)))
    print(f"=== {fname} ({len(calls)} calls across {len(funcs)} functions) ===")
    for fn in funcs:
        fn_calls = [c for c in calls if c["func"] == fn]
        line_nums = ", ".join(str(c["lineno"]) for c in fn_calls)
        print(f"  - {fn} ({len(fn_calls)} calls): lines [{line_nums}]")
