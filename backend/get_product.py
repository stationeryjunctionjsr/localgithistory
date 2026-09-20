import asyncio
from app.db.mysql_product_dao import MySQLProductDAO

async def main():
    dao = MySQLProductDAO()
    products = await dao.findAll()
    if products:
        print("Product ID:", products[0].id)
    else:
        print("No products found")

asyncio.run(main())
