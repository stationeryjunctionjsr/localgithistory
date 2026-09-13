import re

with open('backend/app/repositories/user_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of complex regex, just replace the exact block
block = '''        user = {
            "userId": user_id,  # Keep numeric ID for internal use
            "userIdFormatted": user_id_formatted,  # Display format: USER-1, USER-2, etc.
            "name": name,
            "email": email_val,
            "password": hashed_password,
            "role": role,
            "phone": user_data.get("phone", ""),
            "companyName": user_data.get("companyName", ""),
            "address": user_data.get("address", {}),
            "savedAddresses": user_data.get("savedAddresses", []),
            "isActive": user_data.get("isActive", True),
            "approvalStatus": user_data.get("approvalStatus", approval_status),
            "isDeactivated": user_data.get("isDeactivated", False),
            "creditLimit": user_data.get("creditLimit", 0),
            "creditUsed": user_data.get("creditUsed", 0),
            "paymentTerms": user_data.get("paymentTerms", "30"),
            "assignedSalesperson": user_data.get("assignedSalesperson"),
            "referralCode": referral_code,
            "isEmailVerified": user_data.get("isEmailVerified", False),
        }

        # If an address is provided, add it to savedAddresses if not already there
        if user["address"] and user["address"] not in user["savedAddresses"]:
            user["savedAddresses"].append(user["address"])

        return await self.storage.create(UserInternalCreate(**user))'''

new_block = '''        user_model = UserInternalCreate(
            userId=user_id,
            userIdFormatted=user_id_formatted,
            name=name,
            email=email_val,
            password=hashed_password,
            role=role,
            phone=user_data.get("phone", ""),
            companyName=user_data.get("companyName", ""),
            address=user_data.get("address", {}),
            savedAddresses=user_data.get("savedAddresses", []),
            isActive=user_data.get("isActive", True),
            approvalStatus=user_data.get("approvalStatus", approval_status),
            isDeactivated=user_data.get("isDeactivated", False),
            creditLimit=user_data.get("creditLimit", 0),
            creditUsed=user_data.get("creditUsed", 0),
            paymentTerms=user_data.get("paymentTerms", "30"),
            assignedSalesperson=user_data.get("assignedSalesperson"),
            referralCode=referral_code,
            isEmailVerified=user_data.get("isEmailVerified", False),
        )

        if user_model.address and user_model.address not in user_model.savedAddresses:
            user_model.savedAddresses.append(user_model.address)

        return await self.storage.create(user_model)'''

content = content.replace(block, new_block)

# Also fix update
update_block = '''        return await self.storage.update(id, UserInternalUpdate(**update_data))'''
update_new = '''        if isinstance(update_data, dict):
            update_data = UserInternalUpdate(**update_data)
        return await self.storage.update(id, update_data)'''
content = content.replace(update_block, update_new)

with open('backend/app/repositories/user_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
