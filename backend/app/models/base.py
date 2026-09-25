from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        coerce_numbers_to_str=True,
        from_attributes=True
    )
