import os

filepath = 'app/models/ad.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace CamelCase alias fields with CamelBaseModel
text = text.replace('class Ad(BaseModel):', 'from app.models.base import CamelBaseModel\nclass Ad(CamelBaseModel):')

# Remove stats
text = text.replace("    stats: Optional[AdStats] = Field(default=None, alias='stats')\n", "")
text = text.replace("    impressions: int = Field(default=None, alias='impressions')", "    stat_impressions: Optional[int] = Field(default=0)")
text = text.replace("    clicks: int = Field(default=None, alias='clicks')", "    stat_clicks: Optional[int] = Field(default=0)")
text = text.replace("    leads: int = Field(default=None, alias='leads')", "    stat_leads: Optional[int] = Field(default=0)")
text = text.replace("    purchases: int = Field(default=None, alias='purchases')", "    stat_purchases: Optional[int] = Field(default=0)")
text = text.replace("    add_to_cart: int = Field(default=None, alias='add_to_cart')", "    stat_add_to_cart: Optional[int] = Field(default=0)")
text = text.replace("    conversions: int = Field(default=None, alias='conversions')", "    stat_conversions: Optional[int] = Field(default=0)")
text = text.replace("    conversion_value: float = Field(default=None, alias='conversion_value')", "    stat_conversion_value: Optional[float] = Field(default=0.0)")
text = text.replace("    ctr: float = Field(default=None, alias='ctr')", "    stat_ctr: Optional[float] = Field(default=0.0)")
text = text.replace("    cvr: float = Field(default=None, alias='cvr')", "    stat_cvr: Optional[float] = Field(default=0.0)")

# Remove all hardcoded aliases because CamelBaseModel does it automatically
import re
text = re.sub(r",\s*alias='[^']+'", "", text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
