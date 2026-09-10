import sys
import asyncio
import os
import socket
from dotenv import load_dotenv

# Force IPv4 resolution to prevent tunnel timeouts
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

sys.path.append(r'c:\Ecommerce app\backend')
load_dotenv(r'c:\Ecommerce app\backend\.env')

from app.db.mysql_product_dao import MySQLProductDAO

async def test_dao():
    dao = MySQLProductDAO()
    try:
        products = await dao.findAll()
        print("SUCCESS! findAll() executed without errors.")
        print(f"Returned {len(products)} products.")
    except Exception as e:
        print(f"ERROR during findAll(): {e}")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(test_dao())
