"""
MySQL DAO for CategoryHeads - backwards-compatible wrapper for MySQLDivisionDAO.
Internally, the taxonomy tier is Division.
"""

from app.db.mysql_division_dao import MySQLDivisionDAO

class MySQLCategoryHeadDAO(MySQLDivisionDAO):
    """Backwards-compatible alias for MySQLDivisionDAO."""
    pass
