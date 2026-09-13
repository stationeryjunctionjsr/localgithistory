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

class Otp(BaseModel):
    pass
