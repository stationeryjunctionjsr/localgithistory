with open('backend/app/routers/users.py', 'a') as f:
    f.write('''
class PaymentDetailsUpdate(BaseModel):
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    bankAccountNumber: Optional[str] = None
    bankIfscCode: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None

@router.put('/me/payment-details', response_model=UserResponse)
async def update_my_payment_details(data: PaymentDetailsUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ('wholesaler', 'valet'):
        raise HTTPException(status_code=403, detail='Only sellers and valets can update payment details')
    updated = await user_repository.update(str(current_user.id), UserUpdate(
        upiId=data.upiId,
        qrCodeUrl=data.qrCodeUrl,
        bankAccountNumber=data.bankAccountNumber,
        bankIfscCode=data.bankIfscCode,
        bankAccountHolder=data.bankAccountHolder,
        bankName=data.bankName,
    ))
    return updated

from app.models.schemas import PaymentDetailsResponse

@router.get('/{user_id}/payment-details', response_model=PaymentDetailsResponse)
async def get_user_payment_details(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return PaymentDetailsResponse(
        upiId=user.upi_id,
        qrCodeUrl=user.qr_code_url,
        bankAccountNumber=user.bank_account_number,
        bankIfscCode=user.bank_ifsc_code,
        bankAccountHolder=user.bank_account_holder,
        bankName=user.bank_name,
    )
''')
