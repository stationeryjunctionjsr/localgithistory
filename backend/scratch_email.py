import asyncio
from app.services.email_service import email_service

def test():
    res = email_service.send_email("dilawariresham29@gmail.com", "Test", "Test body")
    print("Result:", res)

if __name__ == "__main__":
    test()
