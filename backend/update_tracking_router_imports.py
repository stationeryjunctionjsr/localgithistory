import re
filepath = r"app\routers\tracking.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("from app.models.base import CamelBaseModel, Field, ConfigDict", "from app.models.base import CamelBaseModel\nfrom pydantic import Field, ConfigDict")
text = text.replace("from pydantic import BaseModel, Field", "from pydantic import BaseModel, Field, ConfigDict")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
