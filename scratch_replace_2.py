import re

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

commission_models = """
class SellerOverrideResponse(BaseModel):
    id: str
    commissionOverridePct: Optional[float] = None
    message: str
"""

delivery_models = """
class LocationChargeResponse(BaseModel):
    charge: float = 0.0
    minCartValue: float = 0.0
    source: str = ""
    deliveryCharge: Optional[Any] = None
    isApplicableToRole: bool = True
    appliedTier: Optional[Any] = None
    urgentDeliveryAvailable: bool = False
    urgentDeliveryCharge: Optional[float] = None
    gstPercentage: float = 0.0
    gstAmount: float = 0.0
    totalCharge: float = 0.0

class ServiceableSeller(BaseModel):
    id: str
    name: str
    companyName: str
    city: Optional[str] = None
    allowUrgentDelivery: bool = False
    allowDeliverySlots: bool = False

class ServiceabilityResponse(BaseModel):
    isServiceable: bool
    pincode: str
    userRole: Optional[str] = None
    sellerCount: int = 0
    serviceableSellers: List[ServiceableSeller] = []
    slotBookingAvailable: bool = False
    availableDates: List[Any] = []
    urgentDeliveryAvailable: bool = False

class UploadCsvResponse(BaseModel):
    message: str
    errors: List[str] = []
"""

replace_in_file("backend/app/routers/commission.py", {
    "class CommissionPreviewResponse(BaseModel):": commission_models + "\nclass CommissionPreviewResponse(BaseModel):",
    "@router.put(\"/sellers/{seller_id}/override\", response_model=Dict[str, Any])": "@router.put(\"/sellers/{seller_id}/override\", response_model=SellerOverrideResponse)"
})

replace_in_file("backend/app/routers/delivery_charges.py", {
    "from app.utils.cache import cache": "from app.utils.cache import cache" + "\nfrom pydantic import BaseModel\n" + delivery_models,
    "@router.get(\"/location\", response_model=Dict[str, Any])": "@router.get(\"/location\", response_model=LocationChargeResponse)",
    "@router.get(\"/check-serviceability\", response_model=Dict[str, Any])": "@router.get(\"/check-serviceability\", response_model=ServiceabilityResponse)",
    "@router.post(\"/upload-csv\", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])": "@router.post(\"/upload-csv\", status_code=status.HTTP_200_OK, response_model=UploadCsvResponse)"
})

print("Done part 2")
