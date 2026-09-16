import os
filepath = 'backend/app/db/mysql_flat_base_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return self.schema_cls(**out) if self.schema_cls else out',
    '''cls = getattr(self, "schema_cls", getattr(self, "pydantic_model", None))
        return cls(**out) if cls else out'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
