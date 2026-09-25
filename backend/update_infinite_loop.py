import re

filepath = r"app\db\mysql_user_dao.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'isSellerAdmin'", "'is_seller_admin'")
text = text.replace("'isOnDuty'", "'is_on_duty'")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

filepath_ref = r"app\utils\referral.py"
with open(filepath_ref, 'r', encoding='utf-8') as f:
    text_ref = f.read()
text_ref = text_ref.replace("'referralCode'", "'referral_code'")
with open(filepath_ref, 'w', encoding='utf-8') as f:
    f.write(text_ref)

