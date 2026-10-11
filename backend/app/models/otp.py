from typing import List, Optional
from pydantic import BaseModel, Field

class Bundle(BaseModel):
    id: str = ""

class EmailOtp(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    device_key: Optional[str] = None
    otp: str
    verify_attempts: int = 0
    created_at: float = 0.0
    expires_at: float = 0.0
    last_sent_at: float = 0.0

class FaqSection(BaseModel):
    pass

class Otp(BaseModel):
    id: Optional[int] = None
    phone: Optional[str] = None
    device_key: Optional[str] = None
    otp: str
    verify_attempts: int = 0
    created_at: float = 0.0
    expires_at: float = 0.0
    last_sent_at: float = 0.0
