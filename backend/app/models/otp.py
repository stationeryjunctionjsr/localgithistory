from typing import List, Optional
from typing import Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Bundle(DictCompatibleModel):
    id: str = Field(default="", alias="_id")

class EmailOtp(DictCompatibleModel):
    pass

class FaqSection(DictCompatibleModel):
    pass

class Otp(DictCompatibleModel):
    pass
