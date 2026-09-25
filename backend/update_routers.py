import re

with open('app/routers/valet_payout.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_enrich = '''async def _enrich_with_valet(doc: dict) -> dict:
    valet = await user_repository.findById(doc.get("valetId"))
    if valet:
        doc["valetName"] = valet.name
        doc["valetPhone"] = valet.phone
        doc["valetUpiId"] = valet.upi_id
        doc["valetQrCodeUrl"] = valet.qr_code_url
        doc["valetBankAccountNumber"] = valet.bank_account_number
        doc["valetBankIfscCode"] = valet.bank_ifsc_code
        doc["valetBankAccountHolder"] = valet.bank_account_holder
        doc["valetBankName"] = valet.bank_name
    return doc'''

new_enrich = '''async def _enrich_with_valet(doc: ValetPayoutDetailResponse) -> ValetPayoutDetailResponse:
    valet = await user_repository.findById(doc.valet_id)
    if valet:
        doc.valetName = valet.name
        doc.valetPhone = valet.phone
        doc.valetUpiId = valet.upi_id
        doc.valetQrCodeUrl = valet.qr_code_url
        doc.valetBankAccountNumber = valet.bank_account_number
        doc.valetBankIfscCode = valet.bank_ifsc_code
        doc.valetBankAccountHolder = valet.bank_account_holder
        doc.valetBankName = valet.bank_name
    return doc'''
    
text = text.replace(old_enrich, new_enrich)

# Replace existing.get("notes") with existing.notes
text = text.replace('existing.get("notes")', 'existing.notes')
text = text.replace('existing.get("valetId")', 'existing.valet_id')

with open('app/routers/valet_payout.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open('app/routers/seller_payouts.py', 'r', encoding='utf-8') as f:
    stext = f.read()

old_senrich = '''async def _enrich_with_seller(doc: dict) -> dict:
    seller = await user_repository.findById(doc.get("sellerId"))
    if seller:
        doc["sellerName"] = seller.company_name or seller.name or ""
        doc["sellerUpiId"] = seller.upi_id
        doc["sellerQrCodeUrl"] = seller.qr_code_url
        doc["sellerBankAccountNumber"] = seller.bank_account_number
        doc["sellerBankIfscCode"] = seller.bank_ifsc_code
        doc["sellerBankAccountHolder"] = seller.bank_account_holder
        doc["sellerBankName"] = seller.bank_name
    return doc'''
    
new_senrich = '''async def _enrich_with_seller(doc: SellerPayoutDetailResponse) -> SellerPayoutDetailResponse:
    seller = await user_repository.findById(doc.seller_id)
    if seller:
        doc.sellerName = seller.company_name or seller.name or ""
        doc.sellerUpiId = seller.upi_id
        doc.sellerQrCodeUrl = seller.qr_code_url
        doc.sellerBankAccountNumber = seller.bank_account_number
        doc.sellerBankIfscCode = seller.bank_ifsc_code
        doc.sellerBankAccountHolder = seller.bank_account_holder
        doc.sellerBankName = seller.bank_name
    return doc'''

stext = stext.replace(old_senrich, new_senrich)
stext = stext.replace('existing.get("notes")', 'existing.notes')
stext = stext.replace('existing.get("sellerId")', 'existing.seller_id')

with open('app/routers/seller_payouts.py', 'w', encoding='utf-8') as f:
    f.write(stext)

print("SUCCESS")
