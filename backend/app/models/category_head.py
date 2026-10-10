"""
CategoryHead models - backwards-compatible aliases for Division models.
Internally, the taxonomy tier is Division.
Admin-facing, it is Super Category.
"""

from app.models.division import (
    Division as CategoryHead,
    DivisionBase as CategoryHeadBase,
    DivisionCreate as CategoryHeadCreate,
    DivisionUpdate as CategoryHeadUpdate,
    DivisionResponse as CategoryHeadResponse,
    DivisionInternal as CategoryHeadInternal,
    DivisionInternalCreate as CategoryHeadInternalCreate,
    DivisionInternalUpdate as CategoryHeadInternalUpdate,
)

__all__ = [
    "CategoryHead",
    "CategoryHeadBase",
    "CategoryHeadCreate",
    "CategoryHeadUpdate",
    "CategoryHeadResponse",
    "CategoryHeadInternal",
    "CategoryHeadInternalCreate",
    "CategoryHeadInternalUpdate",
]
