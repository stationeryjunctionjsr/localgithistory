from typing import List, Optional
from typing import Any, Dict
from pydantic import Field
from pydantic import BaseModel

class FaqItem(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None

class Bundle(BaseModel):
    id: str = ""

class EmailOtp(BaseModel):
    pass

class FaqSection(BaseModel):
    pass

class FaqSectionInternalCreate(BaseModel):
    title: str = ""
    orderIndex: Optional[int] = 0
    isActive: Optional[bool] = True
    icon: Optional[str] = None
    items: Optional[List[FaqItem]] = []

class FaqSectionInternalUpdate(BaseModel):
    title: Optional[str] = None
    orderIndex: Optional[int] = None
    isActive: Optional[bool] = None
    icon: Optional[str] = None
    items: Optional[List[FaqItem]] = None

class FaqSectionResponse(BaseModel):
    id: Optional[str] = ""
    title: str = ""
    orderIndex: Optional[int] = 0
    isActive: bool = True
    icon: Optional[str] = None
    items: Optional[List[FaqItem]] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class Otp(BaseModel):
    pass
