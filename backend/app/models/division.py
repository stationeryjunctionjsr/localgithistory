from datetime import datetime
from typing import List, Optional, Union
from pydantic import ConfigDict, Field
from app.models.base import CamelBaseModel


class DivisionCategoryTag(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    id: Union[int, str]
    external_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = Field(True, alias="isActive")


class Division(CamelBaseModel):
    id: str = Field(default=None)
    external_id: Optional[str] = Field(default=None)
    name: str
    description: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    category_tag_ids: List[int] = Field(default_factory=list)
    category_tags: List[DivisionCategoryTag] = Field(default_factory=list)
    category_count: int = Field(default=0)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class DivisionBase(CamelBaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = Field(default=0)
    is_active: bool = True
    category_tag_ids: Optional[List[int]] = Field(default_factory=list)


class DivisionCreate(DivisionBase):
    pass


class DivisionUpdate(CamelBaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    category_tag_ids: Optional[List[int]] = None


class DivisionResponse(CamelBaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    category_tag_ids: List[int] = Field(default_factory=list)
    category_tags: List[DivisionCategoryTag] = Field(default_factory=list)
    category_tag_names: List[str] = Field(default_factory=list)
    category_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DivisionInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    id: Optional[str] = None
    external_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    category_tag_ids: List[int] = Field(default_factory=list)
    category_tags: List[DivisionCategoryTag] = Field(default_factory=list)
    category_tag_names: List[str] = Field(default_factory=list)
    category_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DivisionInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    category_tag_ids: Optional[List[int]] = None


class DivisionInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    category_tag_ids: Optional[List[int]] = None
