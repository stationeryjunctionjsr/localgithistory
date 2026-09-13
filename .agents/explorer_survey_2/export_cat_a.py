import json

with open("c:/Ecommerce app/.agents/explorer_survey_2/classified_calls.json", "r", encoding="utf-8") as f:
    calls = json.load(f)

by_file = {}
for c in calls:
    by_file.setdefault(c["file"], []).append(c)

with open("c:/Ecommerce app/.agents/explorer_survey_2/category_a_details.json", "w", encoding="utf-8") as out:
    cat_a_by_file = {}
    for fname, fcalls in sorted(by_file.items()):
        cat_a_calls = [c for c in fcalls if c["category"] == "Category A"]
        if cat_a_calls:
            cat_a_by_file[fname] = cat_a_calls
    json.dump(cat_a_by_file, out, indent=2)

print(f"Dumped details for {len(cat_a_by_file)} files with Category A calls.")
