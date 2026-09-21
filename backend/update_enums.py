with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('    CUSTOMER = "customer"\n    VALET = "valet"', '    CUSTOMER = "customer"\n    VALET = "valet"\n    SELLER = "seller"\n    SELLER_ADMIN = "seller_admin"')

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
