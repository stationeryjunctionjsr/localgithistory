filename = 'app/db/mysql_cart_dao.py'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace(
    "await session.execute(",
    "print(f'\\n[DEBUG] MySQLCartDAO.create: user_id_raw={user_id_raw}, uid={uid}')\n            await session.execute(",
    1
)

with open(filename, 'w') as f:
    f.write(content)
