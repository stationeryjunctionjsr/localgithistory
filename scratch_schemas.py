import os

tfile = 'backend/app/models/schemas.py'
with open(tfile, 'r', encoding='utf-8') as src:
    content = src.read()

target1 = """    valetId: Optional[str] = None
    valet: Optional[Dict[str, Any]] = None  # populated valet
    user: Optional[Dict[str, Any]] = None  # populated user"""

replacement1 = """    valetId: Optional[str] = None
    valet: Optional[Dict[str, Any]] = None  # populated valet
    valetDeclineHistory: Optional[List[str]] = None
    valetCascadeCount: Optional[int] = None
    valetAssignedAt: Optional[str] = None
    user: Optional[Dict[str, Any]] = None  # populated user"""

content = content.replace(target1, replacement1)

target2 = """class ReturnRequestStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned\""""

replacement2 = """class ReturnRequestStatus(str, Enum):
    PENDING = "pending"
    PENDING_VALET = "pending_valet"
    ASSIGNED = "assigned\""""

content = content.replace(target2, replacement2)

with open(tfile, 'w', encoding='utf-8') as out:
    out.write(content)
print("Updated schemas.py")
