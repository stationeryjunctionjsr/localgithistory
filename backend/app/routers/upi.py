from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse, UPIDetailsResponse, UploadQRResponse, UserUpdate
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.config import upi
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.logger import logger

router = APIRouter()


class UPIUpdateRequest(BaseModel):
    upiId: str
    qrCodeUrl: Optional[str] = None


@router.get("/details", response_model=UPIDetailsResponse)
async def get_upi_details(current_user: User = Depends(get_current_user)):
    # Find super admin user
    super_admin = await user_repository.findOne({"role": "super_admin"})
    if super_admin and super_admin.upi_id and super_admin.qr_code_url:
        return {
            "upiId": super_admin.upi_id,
            "qrCodeUrl": super_admin.qr_code_url,
            "instructions": "Scan the QR code or use the UPI ID to make payment. Upload the payment screenshot before placing the order.",
        }

    # Fallback to config if not set in profile
    return {
        "upiId": upi.UPI_ID,
        "qrCodeUrl": upi.UPI_QR_CODE_URL,
        "instructions": "Scan the QR code or use the UPI ID to make payment. Upload the payment screenshot before placing the order.",
    }


@router.put("/details", response_model=UPIDetailsResponse)
async def update_upi_details(upi_data: UPIUpdateRequest, current_user: User = Depends(require_super_admin)):
    """Update UPI payment details (Super Admin only)"""
    if not upi_data.upi_id:
        raise HTTPException(status_code=400, detail="UPI ID is required")

    # Find super admin user
    super_admin = await user_repository.findOne({"role": "super_admin"})
    if not super_admin:
        raise HTTPException(status_code=404, detail="Super admin not found")

    # Update UPI details
    await user_repository.update(super_admin.id, UserUpdate(upiId=upi_data.upi_id, qrCodeUrl=upi_data.qr_code_url))

    return {"message": "UPI details updated successfully", "upiId": upi_data.upi_id, "qrCodeUrl": upi_data.qr_code_url}


@router.post("/upload-qr", status_code=status.HTTP_200_OK, response_model=UploadQRResponse)
async def upload_upi_qr(image: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    """Upload UPI QR Code image (Super Admin only)"""
    try:
        # Validate file
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        from app.services.oci_storage import upload_image_and_return_path

        path = await upload_image_and_return_path(image, "upi", filename_prefix="qr")
        return {"qrCodeUrl": path}

    except Exception as e:
        logger.error("Error uploading UPI QR: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload QR code")
