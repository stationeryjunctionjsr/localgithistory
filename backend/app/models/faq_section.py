from typing import List, Optional
from typing import Any, Dict
from pydantic import Field
from pydantic import BaseModel

class Bundle(BaseModel):
    id: str = Field(default="", alias="_id")

class EmailOtp(BaseModel):
    pass

class FaqSection(BaseModel):
    pass

class FaqSectionInternalCreate(BaseModel):
    title: str = ""
    orderIndex: Optional[int] = 0
    isActive: Optional[bool] = True
    icon: Optional[str] = None
    items: Optional[List[Any]] = []

class FaqSectionInternalUpdate(BaseModel):
    title: Optional[str] = None
    orderIndex: Optional[int] = None
    isActive: Optional[bool] = None
    icon: Optional[str] = None
    items: Optional[List[Any]] = None

class FaqSectionResponse(BaseModel):
    id: Optional[str] = Field(default="", alias="_id")
    externalId: Optional[str] = None
    title: str = ""
    orderIndex: Optional[int] = 0
    isActive: bool = True
    icon: Optional[str] = None
    items: Optional[List[Any]] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class Otp(BaseModel):
    pass
