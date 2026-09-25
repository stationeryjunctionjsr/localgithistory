import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """              params = {'external_id': external_id, 'user_id_formatted': user_id_formatted, 'name': data.name or 'Customer', 'email': data.email, 'password_hash': data.password, 'role': data.role if data.role is not None else 'customer', 'phone': data.phone or None, 'company_name': data.company_name, 'gst_number': data.gstin, 'is_active': 1 if (data.isActive if data.isActive is not None else True) else 0, 'approval_status': data.approvalStatus if data.approvalStatus is not None else 'approved', 'is_deactivated': 1 if data.isDeactivated else 0, 'credit_limit': data.creditLimit if data.creditLimit is not None else 0, 'credit_used': data.creditUsed if data.creditUsed is not None else 0, 'payment_terms': str(data.paymentTerms if data.paymentTerms is not None else '30'), 'assigned_salesperson': data.assignedSalesperson, 'is_email_verified': 1 if (data.is_email_verified if data.is_email_verified is not None else False) else 0, 'referral_code': data.referral_code, 'is_seller_admin': 1 if data.isSellerAdmin else 0, 'is_on_duty': 1 if data.isOnDuty else 0, 'commission_override_pct': data.commissionOverridePct, 'upi_id': data.upiId, 'qr_code_url': data.qrCodeUrl, 'created_at': now, 'updated_at': now}
              try:
                  await session.execute(text(f'\n                INSERT INTO {self.TABLE} (\n                    external_id, user_id_formatted, name, email, password_hash, role, phone, company_name, gst_number,\n                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\n                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,\n                    is_on_duty, commission_override_pct, upi_id, qr_code_url, created_at, updated_at\n                ) VALUES (\n                    :external_id, :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name, :gst_number,\n                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,\n                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,\n                    :is_on_duty, :commission_override_pct, :upi_id, :qr_code_url, :created_at, :updated_at\n                )\n            '), params)
              except Exception as e:
                  print("CRASH ON MAIN USER INSERT PARAMS:")
                  for k, v in params.items():
                      if isinstance(v, dict):
                          print(f"DICT DETECTED: {k} = {v}")
                  raise e"""

text = re.sub(r"              await session\.execute\(text\(f'\\n                INSERT INTO \{self\.TABLE\} \(\\n                    external_id, user_id_formatted, name, email, password_hash, role, phone, company_name, gst_number,\\n                    is_active, approval_status, is_deactivated, credit_limit, credit_used, payment_terms,\\n                    assigned_salesperson, is_email_verified, referral_code, is_seller_admin,\\n                    is_on_duty, commission_override_pct, upi_id, qr_code_url, created_at, updated_at\\n                \) VALUES \(\\n                    :external_id, :user_id_formatted, :name, :email, :password_hash, :role, :phone, :company_name, :gst_number,\\n                    :is_active, :approval_status, :is_deactivated, :credit_limit, :credit_used, :payment_terms,\\n                    :assigned_salesperson, :is_email_verified, :referral_code, :is_seller_admin,\\n                    :is_on_duty, :commission_override_pct, :upi_id, :qr_code_url, :created_at, :updated_at\\n                \)\\n            '\), \{.*?\}\)", replacement, text, flags=re.DOTALL)

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
