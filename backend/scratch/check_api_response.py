import sys
import os
from pathlib import Path

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from app.models.schemas import CouponResponse
import json

c = {
    "_id": "123",
    "displayId": "DISC-RT-1",
    "typeOfDiscount": "product_discount",
    "discountType": "percentage",
    "discountValue": 10.0,
    "validUntil": "2026-12-31T23:59:59",
    "usedCount": 0,
    "createdAt": "2026-01-01T00:00:00",
    "updatedAt": "2026-01-01T00:00:00"
}
resp = CouponResponse(**c)
print("model_dump():", resp.model_dump())
print("model_dump(by_alias=True):", resp.model_dump(by_alias=True))
