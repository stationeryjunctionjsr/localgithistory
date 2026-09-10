from pydantic import BaseModel, ConfigDict
from typing import ClassVar, Dict, Optional

class DictCompatibleModel(BaseModel):
    """A bridge model that supports fast dictionary-like access via aliases to ease migration."""
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

    def get(self, key: str, default=None):
        actual_key = self._get_alias_map().get(key, key)
        return getattr(self, actual_key, default)

    def __getitem__(self, key: str):
        actual_key = self._get_alias_map().get(key, key)
        if not hasattr(self, actual_key):
            raise KeyError(key)
        return getattr(self, actual_key)

    def __setitem__(self, key: str, value):
        actual_key = self._get_alias_map().get(key, key)
        setattr(self, actual_key, value)

    def keys(self):
        return self._get_alias_map().keys()

    def __contains__(self, key: str):
        return key in self._get_alias_map() or hasattr(self, key)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self.__setitem__(k, v)
