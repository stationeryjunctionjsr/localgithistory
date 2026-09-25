import re

filepath_v = r"app\db\mysql_valet_payout_dao.py"
with open(filepath_v, 'r', encoding='utf-8') as f:
    text_v = f.read()

replacement_v = '''    def _map_row(self, row) -> ValetPayoutDetailResponse:
        d = dict(row._mapping)
        d["id"] = str(d["id"])
        return ValetPayoutDetailResponse.model_validate(d)'''

text_v = re.sub(r'    def _map_row\(self, row\) -> ValetPayoutDetailResponse:.*?updated_at else None,\n        \)', replacement_v, text_v, flags=re.DOTALL)

with open(filepath_v, 'w', encoding='utf-8') as f:
    f.write(text_v)


filepath_s = r"app\db\mysql_seller_payout_dao.py"
with open(filepath_s, 'r', encoding='utf-8') as f:
    text_s = f.read()

replacement_s = '''    def _map_row(self, row) -> SellerPayoutDetailResponse:
        d = dict(row._mapping)
        d["id"] = str(d["id"])
        return SellerPayoutDetailResponse.model_validate(d)'''

text_s = re.sub(r'    def _map_row\(self, row\) -> SellerPayoutDetailResponse:.*?updated_at else None,\n        \)', replacement_s, text_s, flags=re.DOTALL)

with open(filepath_s, 'w', encoding='utf-8') as f:
    f.write(text_s)
