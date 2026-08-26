import re

with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(
    r'"commissionSettings": _dao\(\s*"sj_commission_settings",\s*\{"defaultCommissionPct": "default_commission_pct"\},\s*\{"tiers": "tiers"\}\s*\),',
    "",
    c,
)

c = re.sub(
    r'"valetAvailability": _dao\(\s*"sj_valet_availability",\s*\{"date": "date", "availabilityType": "availability_type"\},\s*\{"slots": "slots", "zones": "zones"\}\s*\),',
    "",
    c,
)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
