"""
CategoryHead repository - backwards-compatible wrapper for DivisionRepository.
"""

from app.repositories.division_repository import DivisionRepository, division_repository

class CategoryHeadRepository(DivisionRepository):
    pass

category_head_repository = division_repository
