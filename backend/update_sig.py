import re

with open('app/routers/valet_payout.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('async def _compute_valet_earnings(valet_id: str, settings: dict, orders: list, returns: list) -> dict:', 'from app.models.schemas import ValetEarningsResponse\nasync def _compute_valet_earnings(valet_id: str, settings: dict, orders: list, returns: list) -> ValetEarningsResponse:')

with open('app/routers/valet_payout.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
