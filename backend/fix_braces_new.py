with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace(
    '"isActive",\n            \n    "stockReservations": _dao(',
    '"isActive",\n            }\n        )\n    ),\n    "stockReservations": _dao(',
)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
