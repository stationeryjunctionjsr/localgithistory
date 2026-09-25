import re

with open('app/repositories/user_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """            isEmailVerified=(user_data.is_email_verified if user_data.is_email_verified is not None else False),
            isOnDuty=getattr(user_data, 'isOnDuty', False),
            isSellerAdmin=getattr(user_data, 'isSellerAdmin', False),
            serviceAreaZones=getattr(user_data, 'serviceAreaZones', []),
            commissionOverridePct=getattr(user_data, 'commissionOverridePct', None),
            upiId=getattr(user_data, 'upiId', None),
            qrCodeUrl=getattr(user_data, 'qrCodeUrl', None),
            gstin=getattr(user_data, 'gstin', None),
            deviceId=user_data.deviceId,"""

text = text.replace('            isEmailVerified=(user_data.is_email_verified if user_data.is_email_verified is not None else False),\n            deviceId=user_data.deviceId,', replacement)

with open('app/repositories/user_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
