import re

def clean_sql(f):
    with open(f, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # We will use regex that matches anything between CREATE TABLE and the ending semicolon for sj_seller_pincodes
    pattern = re.compile(r"CREATE TABLE .sj_seller_pincodes. \([\s\S]*?\) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;", re.DOTALL)
    new_text = pattern.sub("", text)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(new_text)

clean_sql('scripts/schema_mysql.sql')
clean_sql('scripts/schema_mysql.sql.bak')
