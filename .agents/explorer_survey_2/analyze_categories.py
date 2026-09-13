import json

with open("c:/Ecommerce app/.agents/explorer_survey_2/raw_calls.json", "r", encoding="utf-8") as f:
    calls = json.load(f)

by_file = {}
for c in calls:
    by_file.setdefault(c["file"], []).append(c)

with open("c:/Ecommerce app/.agents/explorer_survey_2/non_router_analysis.txt", "w", encoding="utf-8") as out:
    for fname, fcalls in sorted(by_file.items()):
        non_router = [c for c in fcalls if c["caller"] not in ("router", "app")]
        if not non_router:
            continue
        out.write(f"=== {fname} ({len(non_router)} calls) ===\n")
        for c in non_router:
            out.write(f"  L{c['lineno']:4d} | [{c['caller']}] args: ({c['args']}) | in {c['func']}\n")
            out.write(f"     Code: {c['line_str']}\n")
        out.write("\n")

print("Wrote non_router_analysis.txt")
