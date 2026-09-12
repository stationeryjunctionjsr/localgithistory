from pydantic import BaseModel, ConfigDict
from typing import ClassVar, Dict, Optional

class DictCompatibleModel(BaseModel):
    """A bridge model that previously supported fast dictionary-like access. Now strictly Pydantic."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='allow')
    
    _alias_map: ClassVar[Optional[Dict[str, str]]] = None

    @classmethod
    def _get_alias_map(cls) -> Dict[str, str]:
        if cls._alias_map is None:
            cls._alias_map = {
                (field.alias if field.alias else name): name
                for name, field in cls.model_fields.items()
            }
        return cls._alias_map

    def get(self, key, default=None):
        return getattr(self, self._get_alias_map().get(key, key), default)

    def __getitem__(self, key):
        attr_name = self._get_alias_map().get(key, key)
        if not hasattr(self, attr_name):
            raise KeyError(key)
        return getattr(self, attr_name)

    def __setitem__(self, key, value):
        attr_name = self._get_alias_map().get(key, key)
        setattr(self, attr_name, value)

    def __contains__(self, key):
        return hasattr(self, self._get_alias_map().get(key, key))
