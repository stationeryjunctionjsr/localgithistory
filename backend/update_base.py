import os

filepath = r"app\models\base.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

if "coerce_numbers_to_str" not in text:
    text = text.replace(
        "populate_by_name=True,",
        "populate_by_name=True,\n        coerce_numbers_to_str=True,"
    )

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
