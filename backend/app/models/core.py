from pydantic import BaseModel, ConfigDict
from typing import ClassVar, Dict, Optional

class DictCompatibleModel(BaseModel):
    """A bridge model that previously supported fast dictionary-like access. Now strictly Pydantic."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='ignore')
    
    _alias_map: ClassVar[Optional[Dict[str, str]]] = None

    @classmethod
    def _get_alias_map(cls) -> Dict[str, str]:
        if cls._alias_map is None:
            cls._alias_map = {
                (field.alias if field.alias else name): name
                for name, field in cls.model_fields.items()
            }
        return cls._alias_map
