from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class CustomerSegment(DictCompatibleModel):
    sid: Optional[Any] = Field(default=None, alias='sid')
    uid: Optional[Any] = Field(default=None, alias='uid')
