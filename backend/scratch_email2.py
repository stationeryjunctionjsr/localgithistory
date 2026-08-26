import asyncio
from app.services.email_service import email_service

def test():
    print("Email user:", email_service.smtp_user)
    print("Testing override:", email_service._resolve_to_emails("test@example.com"))

if __name__ == "__main__":
    test()
