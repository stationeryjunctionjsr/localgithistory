import os

files = [
    r"c:\Ecommerce app\backend\app\db\mysql_valet_availability_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_seller_request_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_seller_payout_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_tracking_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_product_dao.py",
    r"c:\Ecommerce app\backend\app\db\mysql_saved_for_later_dao.py"
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace("_row_to_dict", "_map_row")
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")

