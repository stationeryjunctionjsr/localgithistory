from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class CustomerSegment(BaseModel):
    sid: Optional[str] = Field(default=None, alias='sid')
    uid: Optional[str] = Field(default=None, alias='uid')
