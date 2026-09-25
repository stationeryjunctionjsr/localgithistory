import re

filepaths = [
    r"app\db\mysql_seller_payout_dao.py",
    r"app\db\mysql_valet_payout_dao.py",
    r"app\db\mysql_sub_order_dao.py"
]

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Fix SQL parameters mismatches
    text = re.sub(r':sellerId', r':seller_id', text)
    text = re.sub(r':valetId', r':valet_id', text)
    text = re.sub(r':periodStart', r':period_start', text)
    text = re.sub(r':periodEnd', r':period_end', text)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

for fp in filepaths:
    try:
        fix_file(fp)
    except Exception as e:
        print(f"Failed {fp}: {e}")
